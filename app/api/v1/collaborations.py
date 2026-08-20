"""Collaborations (crew): list, detail (S05), deposits (S10), completion,
deliverables, and mutual reviews (S05a)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat.models import Conversation
from app.domains.collaborations import service as collab_service
from app.domains.collaborations.models import (
    Collaboration,
    CollaborationMember,
    CompletionConfirmation,
)
from app.domains.deposits.models import DepositAgreement, DepositParty
from app.domains.notifications.models import Notification
from app.domains.profiles import service as profiles
from app.domains.profiles.models import Profile
from app.domains.reputation.models import Review, TrustEvent
from app.domains.signals.models import Signal
from app.envelope import ok
from app.errors import ProductError
from app.platform.authz import Identity, get_identity, require_profile
from app.platform.db import get_db_session
from app.settings import Settings, get_settings
from pangaea_ai.modules import deposit as m7

router = APIRouter(prefix="/api/v1", tags=["collaborations"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
IdentityDep = Annotated[Identity, Depends(get_identity)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


class DepositProposal(BaseModel):
    amount_minor: int = Field(gt=0)


class DeliverableInput(BaseModel):
    file_name: str = Field(min_length=1, max_length=120)


class ReviewInput(BaseModel):
    reviewee_profile_id: UUID
    rating: str = Field(pattern="^(POSITIVE|NEUTRAL|NEGATIVE)$")
    tags: list[str] = Field(default_factory=list, max_length=5)
    comment: str = Field(default="", max_length=500)


async def _agreement_payload(
    session: AsyncSession, agreement: DepositAgreement | None, viewer_profile_id: UUID
) -> dict | None:
    if agreement is None:
        return None
    parties = list(
        (
            await session.execute(
                select(DepositParty).where(DepositParty.agreement_id == agreement.id)
            )
        ).scalars()
    )
    party_payload = []
    for party in parties:
        profile = await session.get(Profile, party.profile_id)
        party_payload.append(
            {
                "profile_id": str(party.profile_id),
                "name": profile.display_name if profile else "?",
                "agreed": party.agreed_at is not None,
                "funded": party.funded_at is not None,
                "refunded": party.refunded_at is not None,
                "me": party.profile_id == viewer_profile_id,
            }
        )
    return {
        "id": str(agreement.id),
        "status": agreement.status,
        "currency": agreement.currency,
        "amount_minor_per_party": agreement.amount_minor_per_party,
        "total_minor": agreement.amount_minor_per_party * len(parties),
        "terms_hash": agreement.terms_hash,
        "parties": party_payload,
    }


async def _collaboration_payload(
    session: AsyncSession,
    collaboration: Collaboration,
    viewer_profile_id: UUID,
    settings,
) -> dict:
    members = await collab_service.members_of(session, collaboration.id)
    member_payload = []
    for member in members:
        profile = await session.get(Profile, member.profile_id)
        if profile is None:
            continue
        projection = await profiles.trust_of(session, profile.id, settings)
        completed_delta = None
        if collaboration.status == "COMPLETED" and projection.value is not None:
            completed_delta = round(projection.value - 1.2, 1)
        member_payload.append(
            {
                "profile_id": str(profile.id),
                "name": profile.display_name,
                "initials": profiles.initials_of(profile.display_name),
                "palette": profiles.palette_of(profile.id),
                "role_label": member.role_label,
                "is_requester": member.is_requester,
                "me": profile.id == viewer_profile_id,
                "city_code": profile.city_code,
                "locale": profile.locale,
                "trust": {
                    "value": projection.value,
                    "status": projection.status,
                    "before_completion": completed_delta,
                },
            }
        )
    conversation = (
        await session.execute(
            select(Conversation).where(Conversation.collaboration_id == collaboration.id)
        )
    ).scalar_one_or_none()
    agreement = (
        await session.execute(
            select(DepositAgreement).where(DepositAgreement.collaboration_id == collaboration.id)
        )
    ).scalar_one_or_none()
    confirmations = set(
        (
            await session.execute(
                select(CompletionConfirmation.profile_id).where(
                    CompletionConfirmation.collaboration_id == collaboration.id
                )
            )
        ).scalars()
    )
    signal = await session.get(Signal, collaboration.signal_id)
    reviews = list(
        (
            await session.execute(select(Review).where(Review.collaboration_id == collaboration.id))
        ).scalars()
    )
    return {
        "id": str(collaboration.id),
        "title": collaboration.title,
        "status": collaboration.status,
        "deposit_applies": collaboration.deposit_applies,
        "signal_id": str(collaboration.signal_id),
        "signal_type": signal.signal_type if signal else None,
        "duration_weeks": signal.duration_weeks if signal else None,
        "conversation_id": str(conversation.id) if conversation else None,
        "members": member_payload,
        "deposit": await _agreement_payload(session, agreement, viewer_profile_id),
        "deliverables": await collab_service.deliverables_of(session, collaboration.id),
        "my_confirmation": viewer_profile_id in confirmations,
        "confirmed_count": len(confirmations),
        "completed_at": (
            collaboration.completed_at.isoformat() if collaboration.completed_at else None
        ),
        "my_review_targets": [
            member["profile_id"]
            for member in member_payload
            if not member["me"]
            and not any(
                str(review.reviewer_profile_id) == str(viewer_profile_id)
                and str(review.reviewee_profile_id) == member["profile_id"]
                for review in reviews
            )
        ],
    }


@router.get("/collaborations")
async def list_collaborations(session: SessionDep, identity: IdentityDep, settings: SettingsDep):
    profile = require_profile(identity)
    rows = list(
        (
            await session.execute(
                select(Collaboration)
                .join(
                    CollaborationMember,
                    CollaborationMember.collaboration_id == Collaboration.id,
                )
                .where(CollaborationMember.profile_id == profile.id)
                .order_by(Collaboration.created_at.desc())
            )
        ).scalars()
    )
    return ok(
        [
            await _collaboration_payload(session, collaboration, profile.id, settings)
            for collaboration in rows
        ]
    )


@router.get("/collaborations/{collaboration_id}")
async def collaboration_detail(
    collaboration_id: UUID, session: SessionDep, identity: IdentityDep, settings: SettingsDep
):
    profile = require_profile(identity)
    collaboration = await collab_service.require_member(session, collaboration_id, profile.id)
    return ok(await _collaboration_payload(session, collaboration, profile.id, settings))


@router.post("/collaborations/{collaboration_id}/deposit-proposals", status_code=201)
async def propose_deposit(
    collaboration_id: UUID,
    body: DepositProposal,
    session: SessionDep,
    identity: IdentityDep,
    settings: SettingsDep,
):
    profile = require_profile(identity)
    collaboration = await collab_service.require_member(session, collaboration_id, profile.id)
    signal = await session.get(Signal, collaboration.signal_id)
    clause_keys = ["DEPOSIT", "DELIVERABLE_HASH", "ASYNC_COLLAB", "DISSOLUTION"]
    if signal and signal.license_risk_flagged:
        clause_keys.insert(1, "DERIVATIVE_IP")
    agreement = await collab_service.propose_deposit(
        session,
        collaboration,
        acting_profile=profile,
        amount_minor=body.amount_minor,
        clause_keys=clause_keys,
        settings=settings,
    )
    await session.commit()
    draft = m7.draft(clause_keys, {"amount": f"{body.amount_minor:,}원"})
    return ok(
        {
            "agreement": await _agreement_payload(session, agreement, profile.id),
            "draft": draft,
        }
    )


@router.post("/deposit-agreements/{agreement_id}/agree")
async def agree_deposit(agreement_id: UUID, session: SessionDep, identity: IdentityDep):
    profile = require_profile(identity)
    agreement = await session.get(DepositAgreement, agreement_id)
    if agreement is None:
        raise ProductError(code="DEPOSIT_NOT_FOUND", message="agreement not found", status_code=404)
    await collab_service.agree_deposit(session, agreement, profile_id=profile.id)
    await session.commit()
    return ok(await _agreement_payload(session, agreement, profile.id))


@router.post("/deposit-agreements/{agreement_id}/fund")
async def fund_deposit(agreement_id: UUID, session: SessionDep, identity: IdentityDep):
    profile = require_profile(identity)
    agreement = await session.get(DepositAgreement, agreement_id)
    if agreement is None:
        raise ProductError(code="DEPOSIT_NOT_FOUND", message="agreement not found", status_code=404)
    await collab_service.fund_deposit(session, agreement, profile_id=profile.id)
    await session.commit()
    return ok(await _agreement_payload(session, agreement, profile.id))


@router.post("/collaborations/{collaboration_id}/deliverables", status_code=201)
async def add_deliverable(
    collaboration_id: UUID, body: DeliverableInput, session: SessionDep, identity: IdentityDep
):
    profile = require_profile(identity)
    collaboration = await collab_service.require_member(session, collaboration_id, profile.id)
    await collab_service.add_deliverable(session, collaboration, file_name=body.file_name)
    await session.commit()
    return ok(await collab_service.deliverables_of(session, collaboration.id))


@router.post("/collaborations/{collaboration_id}/completion-confirmations")
async def confirm_completion(
    collaboration_id: UUID, session: SessionDep, identity: IdentityDep, settings: SettingsDep
):
    profile = require_profile(identity)
    collaboration = await collab_service.require_member(session, collaboration_id, profile.id)
    result = await collab_service.confirm_completion(session, collaboration, profile_id=profile.id)
    await session.commit()
    return ok(
        {
            **result,
            "collaboration": await _collaboration_payload(
                session, collaboration, profile.id, settings
            ),
        }
    )


@router.post("/collaborations/{collaboration_id}/reviews", status_code=201)
async def create_review(
    collaboration_id: UUID,
    body: ReviewInput,
    session: SessionDep,
    identity: IdentityDep,
):
    profile = require_profile(identity)
    collaboration = await collab_service.require_member(session, collaboration_id, profile.id)
    if collaboration.status != "COMPLETED":
        raise ProductError(
            code="REVIEW_NOT_ALLOWED",
            message="reviews open after completion",
            status_code=409,
        )
    members = {m.profile_id for m in await collab_service.members_of(session, collaboration.id)}
    if body.reviewee_profile_id not in members or body.reviewee_profile_id == profile.id:
        raise ProductError(code="REVIEW_NOT_ALLOWED", message="invalid reviewee", status_code=409)
    duplicate = (
        await session.execute(
            select(Review).where(
                Review.collaboration_id == collaboration.id,
                Review.reviewer_profile_id == profile.id,
                Review.reviewee_profile_id == body.reviewee_profile_id,
            )
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        raise ProductError(code="REVIEW_NOT_ALLOWED", message="already reviewed", status_code=409)
    review = Review(
        collaboration_id=collaboration.id,
        reviewer_profile_id=profile.id,
        reviewee_profile_id=body.reviewee_profile_id,
        rating=body.rating,
        tags=body.tags,
        comment=body.comment,
    )
    session.add(review)
    session.add(
        TrustEvent(
            profile_id=body.reviewee_profile_id,
            event_key=f"REVIEW_RECEIVED:{body.rating}",
            source_collaboration_id=collaboration.id,
        )
    )
    reviewee = await session.get(Profile, body.reviewee_profile_id)
    if reviewee and reviewee.owner_user_id:
        session.add(
            Notification(
                user_id=reviewee.owner_user_id,
                kind="REVIEW_RECEIVED",
                payload={"rating": body.rating, "title": collaboration.title},
                resource_type="collaboration",
                resource_id=collaboration.id,
            )
        )
    await session.commit()
    return ok({"id": str(review.id)})
