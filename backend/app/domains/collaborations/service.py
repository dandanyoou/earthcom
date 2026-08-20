"""Applications → collaborations → completion → refund → trust, atomically.

The accept path creates the collaboration, membership, and conversation in one
transaction. Completion refunds the promise deposit through the sandbox ledger
(append-only, idempotent) and appends COLLABORATION_COMPLETED trust events —
the only place the demo mutates trust outside seeding.
"""

import hashlib
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat.models import Conversation
from app.domains.collaborations.models import (
    Application,
    Collaboration,
    CollaborationDeliverable,
    CollaborationMember,
    CompletionConfirmation,
)
from app.domains.deposits.models import DepositAgreement, DepositLedgerEntry, DepositParty
from app.domains.notifications.models import Notification
from app.domains.profiles.models import Profile
from app.domains.reputation.models import TrustEvent
from app.domains.signals.models import Signal, SignalRole
from app.errors import ProductError
from app.settings import Settings

DEPOSIT_TYPES = ("WORK", "BOOKING")


def deposit_applies(signal_type: str) -> bool:
    return signal_type in DEPOSIT_TYPES


async def _notify(
    session: AsyncSession,
    *,
    profile: Profile,
    kind: str,
    payload: dict,
    resource_type: str,
    resource_id: UUID,
) -> None:
    if profile.owner_user_id is None:
        return
    session.add(
        Notification(
            user_id=profile.owner_user_id,
            kind=kind,
            payload=payload,
            resource_type=resource_type,
            resource_id=resource_id,
        )
    )


def collaboration_title(signal: Signal) -> str:
    text = signal.raw_text.strip().splitlines()[0]
    return (text[:24] + "…") if len(text) > 24 else text


async def accept_application(
    session: AsyncSession, application: Application, *, acting_profile: Profile
) -> Collaboration:
    signal = await session.get(Signal, application.signal_id)
    if signal is None:
        raise ProductError(code="SIGNAL_NOT_FOUND", message="signal not found", status_code=404)

    # Who may accept: the requester accepts applications; the invitee accepts invitations.
    allowed = (
        signal.requester_profile_id
        if application.direction == "APPLICATION"
        else application.applicant_profile_id
    )
    if acting_profile.id != allowed:
        raise ProductError(
            code="ACTING_PROFILE_FORBIDDEN", message="cannot accept this", status_code=403
        )
    if application.status != "PENDING":
        raise ProductError(
            code="COLLABORATION_INVALID_TRANSITION",
            message="application is not pending",
            status_code=409,
        )

    now = datetime.now(UTC)
    application.status = "ACCEPTED"
    application.decided_at = now

    collaboration = (
        await session.execute(
            select(Collaboration).where(
                Collaboration.signal_id == signal.id,
                Collaboration.status.notin_(("CANCELLED", "COMPLETED")),
            )
        )
    ).scalar_one_or_none()
    applies = deposit_applies(signal.signal_type)
    if collaboration is None:
        collaboration = Collaboration(
            signal_id=signal.id,
            title=collaboration_title(signal),
            status="DEPOSIT_PENDING" if applies else "ACTIVE",
            deposit_applies=applies,
        )
        session.add(collaboration)
        await session.flush()
        session.add(
            CollaborationMember(
                collaboration_id=collaboration.id,
                profile_id=signal.requester_profile_id,
                role_label="요청자",
                is_requester=True,
            )
        )
        session.add(Conversation(collaboration_id=collaboration.id))

    role_label = "참여자"
    if application.role_id is not None:
        role = await session.get(SignalRole, application.role_id)
        if role is not None:
            role_label = role.label
            role.filled_count += 1
    existing_member = (
        await session.execute(
            select(CollaborationMember).where(
                CollaborationMember.collaboration_id == collaboration.id,
                CollaborationMember.profile_id == application.applicant_profile_id,
            )
        )
    ).scalar_one_or_none()
    if existing_member is None:
        session.add(
            CollaborationMember(
                collaboration_id=collaboration.id,
                profile_id=application.applicant_profile_id,
                role_label=role_label,
            )
        )

    if signal.status == "OPEN":
        signal.status = "IN_PROGRESS"
        signal.version += 1

    applicant = await session.get(Profile, application.applicant_profile_id)
    requester = await session.get(Profile, signal.requester_profile_id)
    if applicant and requester:
        target = applicant if application.direction == "APPLICATION" else requester
        await _notify(
            session,
            profile=target,
            kind="APPLICATION_ACCEPTED",
            payload={"title": collaboration.title},
            resource_type="collaboration",
            resource_id=collaboration.id,
        )
    return collaboration


async def members_of(session: AsyncSession, collaboration_id: UUID) -> list[CollaborationMember]:
    return list(
        (
            await session.execute(
                select(CollaborationMember).where(
                    CollaborationMember.collaboration_id == collaboration_id
                )
            )
        ).scalars()
    )


async def require_member(
    session: AsyncSession, collaboration_id: UUID, profile_id: UUID
) -> Collaboration:
    collaboration = await session.get(Collaboration, collaboration_id)
    if collaboration is None:
        raise ProductError(
            code="COLLABORATION_NOT_FOUND", message="collaboration not found", status_code=404
        )
    members = await members_of(session, collaboration_id)
    if profile_id not in {member.profile_id for member in members}:
        raise ProductError(code="ACTING_PROFILE_FORBIDDEN", message="not a member", status_code=403)
    return collaboration


# ── Deposits (sandbox provider — instant, ledgered, idempotent) ──────────────
def terms_hash(amount_minor: int, currency: str, clause_keys: list[str]) -> str:
    seed = f"{amount_minor}|{currency}|{','.join(sorted(clause_keys))}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


async def propose_deposit(
    session: AsyncSession,
    collaboration: Collaboration,
    *,
    acting_profile: Profile,
    amount_minor: int,
    clause_keys: list[str],
    settings: Settings,
) -> DepositAgreement:
    if not collaboration.deposit_applies:
        raise ProductError(
            code="DEPOSIT_NOT_APPLICABLE",
            message="this collaboration has no deposit step",
            status_code=409,
        )
    if amount_minor <= 0 or amount_minor > settings.deposit_cap_amount_minor:
        raise ProductError(
            code="DEPOSIT_CAP_EXCEEDED",
            message="amount exceeds the agreed cap",
            status_code=422,
            details={"cap_minor": settings.deposit_cap_amount_minor},
        )
    existing = (
        await session.execute(
            select(DepositAgreement).where(DepositAgreement.collaboration_id == collaboration.id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ProductError(
            code="DEPOSIT_TERMS_CHANGED", message="a proposal already exists", status_code=409
        )

    agreement = DepositAgreement(
        collaboration_id=collaboration.id,
        status="PROPOSED",
        currency="KRW",
        amount_minor_per_party=amount_minor,
        cap_policy_version=settings.deposit_cap_policy_version,
        terms_hash=terms_hash(amount_minor, "KRW", clause_keys),
    )
    session.add(agreement)
    await session.flush()
    for member in await members_of(session, collaboration.id):
        session.add(DepositParty(agreement_id=agreement.id, profile_id=member.profile_id))
        profile = await session.get(Profile, member.profile_id)
        if profile and profile.id != acting_profile.id:
            await _notify(
                session,
                profile=profile,
                kind="DEPOSIT_UPDATED",
                payload={"status": "PROPOSED", "title": collaboration.title},
                resource_type="collaboration",
                resource_id=collaboration.id,
            )
    return agreement


async def _parties_of(session: AsyncSession, agreement_id: UUID) -> list[DepositParty]:
    return list(
        (
            await session.execute(
                select(DepositParty).where(DepositParty.agreement_id == agreement_id)
            )
        ).scalars()
    )


async def agree_deposit(
    session: AsyncSession, agreement: DepositAgreement, *, profile_id: UUID
) -> DepositAgreement:
    if agreement.status not in ("PROPOSED", "AGREED"):
        raise ProductError(
            code="DEPOSIT_TERMS_CHANGED", message="agreement is not open", status_code=409
        )
    parties = await _parties_of(session, agreement.id)
    me = next((party for party in parties if party.profile_id == profile_id), None)
    if me is None:
        raise ProductError(
            code="ACTING_PROFILE_FORBIDDEN", message="not a deposit party", status_code=403
        )
    me.agreed_at = me.agreed_at or datetime.now(UTC)
    if all(party.agreed_at for party in parties):
        agreement.status = "AGREED"
        agreement.version += 1
    return agreement


async def fund_deposit(
    session: AsyncSession, agreement: DepositAgreement, *, profile_id: UUID
) -> DepositAgreement:
    if agreement.status not in ("AGREED", "FUNDING"):
        raise ProductError(
            code="DEPOSIT_PARTIES_NOT_AGREED",
            message="all parties must agree first",
            status_code=409,
        )
    parties = await _parties_of(session, agreement.id)
    me = next((party for party in parties if party.profile_id == profile_id), None)
    if me is None:
        raise ProductError(
            code="ACTING_PROFILE_FORBIDDEN", message="not a deposit party", status_code=403
        )
    if me.funded_at is None:
        me.funded_at = datetime.now(UTC)
        session.add(
            DepositLedgerEntry(
                agreement_id=agreement.id,
                profile_id=profile_id,
                entry_type="FUND",
                amount_minor=agreement.amount_minor_per_party,
                provider_event_id=f"sbx-fund-{agreement.id}-{profile_id}",
            )
        )
    agreement.status = "FUNDING"
    if all(party.funded_at for party in parties):
        agreement.status = "LOCKED"
        agreement.version += 1
        collaboration = await session.get(Collaboration, agreement.collaboration_id)
        if collaboration and collaboration.status == "DEPOSIT_PENDING":
            collaboration.status = "ACTIVE"
            collaboration.version += 1
    return agreement


async def _refund_deposit(session: AsyncSession, collaboration: Collaboration) -> None:
    agreement = (
        await session.execute(
            select(DepositAgreement).where(
                DepositAgreement.collaboration_id == collaboration.id,
                DepositAgreement.status == "LOCKED",
            )
        )
    ).scalar_one_or_none()
    if agreement is None:
        return
    now = datetime.now(UTC)
    for party in await _parties_of(session, agreement.id):
        if party.refunded_at is None:
            party.refunded_at = now
            session.add(
                DepositLedgerEntry(
                    agreement_id=agreement.id,
                    profile_id=party.profile_id,
                    entry_type="REFUND",
                    amount_minor=agreement.amount_minor_per_party,
                    provider_event_id=f"sbx-refund-{agreement.id}-{party.profile_id}",
                )
            )
    agreement.status = "REFUNDED"
    agreement.version += 1


async def confirm_completion(
    session: AsyncSession, collaboration: Collaboration, *, profile_id: UUID
) -> dict:
    if collaboration.status not in ("ACTIVE", "COMPLETION_PENDING"):
        raise ProductError(
            code="COLLABORATION_INVALID_TRANSITION",
            message="collaboration is not active",
            status_code=409,
        )
    now = datetime.now(UTC)
    existing = (
        await session.execute(
            select(CompletionConfirmation).where(
                CompletionConfirmation.collaboration_id == collaboration.id,
                CompletionConfirmation.profile_id == profile_id,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            CompletionConfirmation(
                collaboration_id=collaboration.id, profile_id=profile_id, confirmed_at=now
            )
        )
        await session.flush()

    members = await members_of(session, collaboration.id)
    confirmed_ids = set(
        (
            await session.execute(
                select(CompletionConfirmation.profile_id).where(
                    CompletionConfirmation.collaboration_id == collaboration.id
                )
            )
        ).scalars()
    )
    everyone_confirmed = {member.profile_id for member in members} <= confirmed_ids
    if everyone_confirmed:
        collaboration.status = "COMPLETED"
        collaboration.completed_at = now
        collaboration.version += 1
        await _refund_deposit(session, collaboration)
        signal = await session.get(Signal, collaboration.signal_id)
        if signal and signal.status in ("IN_PROGRESS", "OPEN"):
            signal.status = "COMPLETED"
            signal.version += 1
        for member in members:
            duplicate = (
                await session.execute(
                    select(TrustEvent).where(
                        TrustEvent.profile_id == member.profile_id,
                        TrustEvent.event_key == "COLLABORATION_COMPLETED",
                        TrustEvent.source_collaboration_id == collaboration.id,
                    )
                )
            ).scalar_one_or_none()
            if duplicate is None:
                session.add(
                    TrustEvent(
                        profile_id=member.profile_id,
                        event_key="COLLABORATION_COMPLETED",
                        source_collaboration_id=collaboration.id,
                    )
                )
            profile = await session.get(Profile, member.profile_id)
            if profile:
                await _notify(
                    session,
                    profile=profile,
                    kind="COLLABORATION_COMPLETED",
                    payload={"title": collaboration.title},
                    resource_type="collaboration",
                    resource_id=collaboration.id,
                )
    else:
        if collaboration.status != "COMPLETION_PENDING":
            collaboration.status = "COMPLETION_PENDING"
            collaboration.version += 1
    return {
        "completed": everyone_confirmed,
        "confirmed_count": len(confirmed_ids),
        "member_count": len(members),
    }


async def deliverables_of(session: AsyncSession, collaboration_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            select(CollaborationDeliverable)
            .where(CollaborationDeliverable.collaboration_id == collaboration_id)
            .order_by(CollaborationDeliverable.position)
        )
    ).scalars()
    return [
        {
            "id": str(row.id),
            "file_name": row.file_name,
            "hash_prefix": f"{row.content_hash[:4]}…{row.content_hash[-4:]}",
        }
        for row in rows
    ]


async def add_deliverable(
    session: AsyncSession, collaboration: Collaboration, *, file_name: str
) -> CollaborationDeliverable:
    rows = await deliverables_of(session, collaboration.id)
    digest = hashlib.sha256(f"{collaboration.id}|{file_name}".encode()).hexdigest()
    deliverable = CollaborationDeliverable(
        collaboration_id=collaboration.id,
        file_name=file_name,
        content_hash=digest,
        position=len(rows),
    )
    session.add(deliverable)
    return deliverable
