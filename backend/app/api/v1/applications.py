"""Applications inbox/outbox (S09) and accept/reject/withdraw transitions."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.collaborations import service as collaborations
from app.domains.collaborations.models import Application
from app.domains.profiles import service as profiles
from app.domains.profiles.models import Profile
from app.domains.signals.models import Signal, SignalRole
from app.envelope import ok
from app.errors import ProductError
from app.platform.authz import Identity, get_identity, require_profile
from app.platform.db import get_db_session
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
IdentityDep = Annotated[Identity, Depends(get_identity)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


async def _payload(session: AsyncSession, application: Application, settings) -> dict:
    signal = await session.get(Signal, application.signal_id)
    applicant = await session.get(Profile, application.applicant_profile_id)
    role_label = None
    if application.role_id:
        role = await session.get(SignalRole, application.role_id)
        role_label = role.label if role else None
    return {
        "id": str(application.id),
        "signal_id": str(application.signal_id),
        "signal_text": signal.raw_text[:80] if signal else "",
        "signal_type": signal.signal_type if signal else None,
        "direction": application.direction,
        "status": application.status,
        "message": application.message,
        "role_label": role_label,
        "applicant": (await profiles.card_of(session, applicant, settings) if applicant else None),
        "created_at": application.created_at.isoformat(),
    }


@router.get("")
async def list_applications(
    session: SessionDep, identity: IdentityDep, settings: SettingsDep, box: str = "received"
):
    profile = require_profile(identity)
    if box == "sent":
        query = select(Application).where(
            Application.applicant_profile_id == profile.id,
            Application.direction == "APPLICATION",
        )
        invites = select(Application).where(
            Application.applicant_profile_id == profile.id,
            Application.direction == "INVITATION",
        )
        rows = list((await session.execute(query)).scalars()) + list(
            (await session.execute(invites)).scalars()
        )
    else:
        my_signals = select(Signal.id).where(Signal.requester_profile_id == profile.id)
        query = select(Application).where(
            Application.signal_id.in_(my_signals), Application.direction == "APPLICATION"
        )
        invites = select(Application).where(
            Application.applicant_profile_id == profile.id,
            Application.direction == "INVITATION",
        )
        rows = list((await session.execute(query)).scalars()) + list(
            (await session.execute(invites)).scalars()
        )
    rows.sort(key=lambda a: a.created_at, reverse=True)
    return ok([await _payload(session, application, settings) for application in rows])


async def _get_application(session: AsyncSession, application_id: UUID) -> Application:
    application = await session.get(Application, application_id)
    if application is None:
        raise ProductError(
            code="APPLICATION_NOT_FOUND", message="application not found", status_code=404
        )
    return application


@router.post("/{application_id}/accept")
async def accept(
    application_id: UUID, session: SessionDep, identity: IdentityDep, settings: SettingsDep
):
    profile = require_profile(identity)
    application = await _get_application(session, application_id)
    collaboration = await collaborations.accept_application(
        session, application, acting_profile=profile
    )
    await session.commit()
    conversation_id = None
    from app.domains.chat.models import Conversation

    conversation = (
        await session.execute(
            select(Conversation).where(Conversation.collaboration_id == collaboration.id)
        )
    ).scalar_one_or_none()
    if conversation:
        conversation_id = str(conversation.id)
    return ok(
        {
            "application": await _payload(session, application, settings),
            "collaboration_id": str(collaboration.id),
            "collaboration_status": collaboration.status,
            "conversation_id": conversation_id,
        }
    )


@router.post("/{application_id}/reject")
async def reject(application_id: UUID, session: SessionDep, identity: IdentityDep):
    profile = require_profile(identity)
    application = await _get_application(session, application_id)
    signal = await session.get(Signal, application.signal_id)
    allowed = (
        signal.requester_profile_id
        if application.direction == "APPLICATION"
        else application.applicant_profile_id
    )
    if profile.id != allowed:
        raise ProductError(
            code="ACTING_PROFILE_FORBIDDEN", message="cannot reject this", status_code=403
        )
    if application.status != "PENDING":
        raise ProductError(
            code="COLLABORATION_INVALID_TRANSITION", message="not pending", status_code=409
        )
    application.status = "REJECTED"
    application.decided_at = datetime.now(UTC)
    await session.commit()
    return ok({"id": str(application.id), "status": application.status})


@router.post("/{application_id}/withdraw")
async def withdraw(application_id: UUID, session: SessionDep, identity: IdentityDep):
    profile = require_profile(identity)
    application = await _get_application(session, application_id)
    if application.applicant_profile_id != profile.id or application.direction != "APPLICATION":
        raise ProductError(
            code="ACTING_PROFILE_FORBIDDEN", message="cannot withdraw this", status_code=403
        )
    if application.status != "PENDING":
        raise ProductError(
            code="COLLABORATION_INVALID_TRANSITION", message="not pending", status_code=409
        )
    application.status = "WITHDRAWN"
    application.decided_at = datetime.now(UTC)
    await session.commit()
    return ok({"id": str(application.id), "status": application.status})
