"""Signals: feed (S01), create/publish (S02), detail (S12), recommendations
(S03), applications and invitations (S03b), direct search (S06)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.collaborations.models import Application, Collaboration
from app.domains.discovery import service as discovery
from app.domains.notifications.models import Notification
from app.domains.profiles import service as profiles
from app.domains.profiles.models import Profile
from app.domains.signals import service as signals_service
from app.domains.signals.models import Signal, SignalRole, SignalSkill
from app.envelope import ok
from app.errors import ProductError
from app.platform.authz import Identity, get_identity, require_profile
from app.platform.db import get_db_session
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1", tags=["signals"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
IdentityDep = Annotated[Identity, Depends(get_identity)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


class RoleForm(BaseModel):
    label: str = Field(min_length=1, max_length=40)
    headcount: int | None = Field(default=None, ge=1, le=50)
    form_position: int = Field(ge=0, le=7)


class SignalCreate(BaseModel):
    raw_text: str = Field(min_length=1, max_length=4000)
    roles_form: list[RoleForm] = Field(default_factory=list, max_length=8)
    edits: dict = Field(default_factory=dict)


class PublishInput(BaseModel):
    inferred_confirmed: bool = False
    license_acknowledged: bool = False
    high_risk_acknowledged: bool = False


class ApplicationCreate(BaseModel):
    role_id: UUID | None = None
    message: str = Field(default="", max_length=1000)
    direction: str = Field(default="APPLICATION", pattern="^(APPLICATION|INVITATION)$")
    invitee_profile_id: UUID | None = None


async def _signal_payload(session: AsyncSession, signal: Signal, settings) -> dict:
    requester = await session.get(Profile, signal.requester_profile_id)
    roles = list(
        (
            await session.execute(
                select(SignalRole)
                .where(SignalRole.signal_id == signal.id)
                .order_by(SignalRole.form_position)
            )
        ).scalars()
    )
    skills = list(
        (
            await session.execute(select(SignalSkill).where(SignalSkill.signal_id == signal.id))
        ).scalars()
    )
    accepted = (
        await session.execute(
            select(Application)
            .where(Application.signal_id == signal.id, Application.status == "ACCEPTED")
            .order_by(Application.decided_at)
        )
    ).scalars()
    accepted = list(accepted)
    accept_latency_seconds = None
    if accepted and signal.published_at and accepted[0].decided_at:
        accept_latency_seconds = int((accepted[0].decided_at - signal.published_at).total_seconds())
    member_faces = []
    for application in accepted[:4]:
        profile = await session.get(Profile, application.applicant_profile_id)
        if profile:
            member_faces.append(
                {
                    "initials": profiles.initials_of(profile.display_name),
                    "palette": profiles.palette_of(profile.id),
                }
            )
    return {
        "id": str(signal.id),
        "signal_type": signal.signal_type,
        "status": signal.status,
        "raw_text": signal.raw_text,
        "urgency": signal.urgency,
        "requires_physical_presence": signal.requires_physical_presence,
        "source_language": signal.source_language,
        "team_cardinality": signal.team_cardinality,
        "target_is_team": signal.target_is_team,
        "duration_weeks": signal.duration_weeks,
        "duration_origin": signal.duration_origin,
        "compensation": {
            "is_paid": signal.compensation_is_paid,
            "amount_minor": signal.compensation_amount_minor,
            "currency": signal.compensation_currency,
            "origin": signal.compensation_origin,
        },
        "license_risk": {
            "flagged": signal.license_risk_flagged,
            "kind": signal.license_risk_kind,
            "acknowledged": signal.license_risk_acknowledged_at is not None,
        },
        "required_credentials": signal.required_credentials,
        "disclaimers": (signal.policy_snapshot or {}).get("disclaimers", []),
        "area_hint": signal.area_hint,
        "published_at": signal.published_at.isoformat() if signal.published_at else None,
        "created_at": signal.created_at.isoformat(),
        "requester": (await profiles.card_of(session, requester, settings) if requester else None),
        "roles": [
            {
                "id": str(role.id),
                "label": role.label,
                "headcount": role.headcount,
                "filled_count": role.filled_count,
                "form_position": role.form_position,
            }
            for role in roles
        ],
        "skills": [
            {
                "name": skill.skill_name,
                "origin": skill.origin,
                "confirmation_status": skill.confirmation_status,
            }
            for skill in skills
        ],
        "accepted_count": len(accepted),
        "accept_latency_seconds": accept_latency_seconds,
        "member_faces": member_faces,
    }


@router.post("/signals", status_code=201)
async def create_signal(
    body: SignalCreate, session: SessionDep, identity: IdentityDep, settings: SettingsDep
):
    profile = require_profile(identity)
    signal = await signals_service.create_draft(
        session,
        requester=profile,
        raw_text=body.raw_text,
        roles_form=[role.model_dump() for role in body.roles_form],
        edits=body.edits,
    )
    await session.commit()
    return ok(await _signal_payload(session, signal, settings))


@router.get("/signals")
async def list_signals(
    session: SessionDep,
    identity: IdentityDep,
    settings: SettingsDep,
    type: str | None = None,
    mine: bool = False,
):
    query = select(Signal).order_by(Signal.created_at.desc()).limit(30)
    if mine:
        query = query.where(Signal.requester_profile_id == identity.profile_id)
    else:
        query = query.where(
            Signal.status.in_(("OPEN", "IN_PROGRESS")), Signal.visibility == "PUBLIC"
        )
    if type in ("HELP", "WORK", "CIRCLE", "BOOKING"):
        query = query.where(Signal.signal_type == type)
    rows = list((await session.execute(query)).scalars())
    return ok([await _signal_payload(session, signal, settings) for signal in rows])


@router.get("/signals/{signal_id}")
async def signal_detail(
    signal_id: UUID, session: SessionDep, identity: IdentityDep, settings: SettingsDep
):
    signal = await session.get(Signal, signal_id)
    if signal is None:
        raise ProductError(code="SIGNAL_NOT_FOUND", message="signal not found", status_code=404)
    if signal.status == "DRAFT" and signal.requester_profile_id != identity.profile_id:
        raise ProductError(
            code="ACTING_PROFILE_FORBIDDEN", message="draft is private", status_code=403
        )
    return ok(await _signal_payload(session, signal, settings))


@router.post("/signals/{signal_id}/publish")
async def publish_signal(
    signal_id: UUID,
    body: PublishInput,
    session: SessionDep,
    identity: IdentityDep,
    settings: SettingsDep,
):
    profile = require_profile(identity)
    signal = await signals_service.get_owned(session, signal_id, profile.id)
    await signals_service.publish(
        session, signal, requester=profile, confirmations=body.model_dump()
    )
    await session.commit()
    return ok(await _signal_payload(session, signal, settings))


@router.get("/signals/{signal_id}/recommendations")
async def signal_recommendations(
    signal_id: UUID, session: SessionDep, identity: IdentityDep, settings: SettingsDep
):
    profile = require_profile(identity)
    signal = await signals_service.get_owned(session, signal_id, profile.id)
    if signal.status not in ("OPEN", "IN_PROGRESS"):
        raise ProductError(
            code="SIGNAL_INVALID_TRANSITION",
            message="publish the signal first",
            status_code=409,
        )
    return ok(await discovery.recommend(session, signal, settings))


@router.post("/signals/{signal_id}/applications", status_code=201)
async def create_application(
    signal_id: UUID,
    body: ApplicationCreate,
    session: SessionDep,
    identity: IdentityDep,
):
    profile = require_profile(identity)
    signal = await session.get(Signal, signal_id)
    if signal is None or signal.status not in ("OPEN", "IN_PROGRESS"):
        raise ProductError(code="SIGNAL_NOT_FOUND", message="signal is not open", status_code=404)

    if body.direction == "INVITATION":
        if signal.requester_profile_id != profile.id:
            raise ProductError(
                code="ACTING_PROFILE_FORBIDDEN",
                message="only the requester can invite",
                status_code=403,
            )
        if body.invitee_profile_id is None:
            raise ProductError(code="VALIDATION_ERROR", message="invitee required", status_code=422)
        applicant_profile_id = body.invitee_profile_id
    else:
        if signal.requester_profile_id == profile.id:
            raise ProductError(
                code="APPLICATION_DUPLICATE",
                message="cannot apply to your own signal",
                status_code=409,
            )
        applicant_profile_id = profile.id

    duplicate = (
        await session.execute(
            select(Application).where(
                Application.signal_id == signal.id,
                Application.applicant_profile_id == applicant_profile_id,
                Application.direction == body.direction,
                Application.status.in_(("PENDING", "ACCEPTED")),
            )
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        raise ProductError(code="APPLICATION_DUPLICATE", message="already applied", status_code=409)

    application = Application(
        signal_id=signal.id,
        applicant_profile_id=applicant_profile_id,
        role_id=body.role_id,
        direction=body.direction,
        message=body.message,
    )
    session.add(application)
    await session.flush()
    target_profile = await session.get(
        Profile,
        (applicant_profile_id if body.direction == "INVITATION" else signal.requester_profile_id),
    )
    if target_profile and target_profile.owner_user_id:
        session.add(
            Notification(
                user_id=target_profile.owner_user_id,
                kind="APPLICATION_RECEIVED",
                payload={
                    "direction": body.direction,
                    "from": profile.display_name,
                },
                resource_type="application",
                resource_id=application.id,
            )
        )
    await session.commit()
    return ok({"id": str(application.id), "status": application.status})


@router.get("/search/profiles")
async def search_profiles_route(
    session: SessionDep, identity: IdentityDep, settings: SettingsDep, q: str = ""
):
    require_profile(identity)
    if not q.strip():
        return ok({"terms": [], "results": [], "total": 0})
    return ok(await discovery.search_profiles(session, q, settings))


@router.get("/home")
async def home(session: SessionDep, identity: IdentityDep, settings: SettingsDep):
    profile = identity.profile
    counts = await profiles.city_counts(session)
    cities = []
    for city_code, timezone_name in (
        ("SEOUL", "Asia/Seoul"),
        ("BERLIN", "Europe/Berlin"),
        ("TOKYO", "Asia/Tokyo"),
        ("LISBON", "Europe/Lisbon"),
        ("NEW_YORK", "America/New_York"),
    ):
        local_time = profiles.local_time_of(timezone_name)
        hour = int(local_time.split(":")[0])
        state = "AWAKE" if 9 <= hour < 22 else ("SLOW" if 6 <= hour < 9 else "SLEEP")
        cities.append(
            {
                "code": city_code,
                "local_time": local_time,
                "state": state,
                "member_count": counts.get(city_code, 0),
            }
        )
    feed_query = (
        select(Signal)
        .where(Signal.status.in_(("OPEN", "IN_PROGRESS")), Signal.visibility == "PUBLIC")
        .order_by(Signal.published_at.desc())
        .limit(12)
    )
    feed = list((await session.execute(feed_query)).scalars())
    open_count = (
        await session.execute(
            select(func.count()).select_from(Signal).where(Signal.status == "OPEN")
        )
    ).scalar_one()
    my_collaborations = 0
    if identity.profile_id:
        from app.domains.collaborations.models import CollaborationMember

        my_collaborations = (
            await session.execute(
                select(func.count())
                .select_from(CollaborationMember)
                .join(Collaboration, Collaboration.id == CollaborationMember.collaboration_id)
                .where(
                    CollaborationMember.profile_id == identity.profile_id,
                    Collaboration.status.notin_(("CANCELLED",)),
                )
            )
        ).scalar_one()
    return ok(
        {
            "profile": (await profiles.card_of(session, profile, settings) if profile else None),
            "cities": cities,
            "signals": [await _signal_payload(session, signal, settings) for signal in feed],
            "open_count": open_count,
            "my_collaboration_count": my_collaborations,
        }
    )
