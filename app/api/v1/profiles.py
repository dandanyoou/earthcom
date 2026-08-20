"""Public profile reads: detail (S03a), trust, reviews, skills catalog."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profiles import service as profiles
from app.domains.profiles.models import Profile, Skill
from app.envelope import ok
from app.errors import ProductError
from app.platform.authz import Identity, get_identity
from app.platform.db import get_db_session
from app.platform.overlap import weekly_overlap_minutes
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1", tags=["profiles"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
IdentityDep = Annotated[Identity, Depends(get_identity)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


async def _get_profile(session: AsyncSession, profile_id: UUID) -> Profile:
    profile = await session.get(Profile, profile_id)
    if profile is None or profile.status not in ("ACTIVE", "HIDDEN"):
        raise ProductError(code="PROFILE_NOT_FOUND", message="profile not found", status_code=404)
    return profile


@router.get("/profiles/{profile_id}")
async def profile_detail(
    profile_id: UUID, session: SessionDep, identity: IdentityDep, settings: SettingsDep
):
    profile = await _get_profile(session, profile_id)
    overlap_minutes = 0
    if identity.profile_id and identity.profile_id != profile.id:
        overlap_minutes = weekly_overlap_minutes(
            await profiles.availability_rules_of(session, identity.profile_id),
            await profiles.availability_rules_of(session, profile.id),
        )
    return ok(
        {
            **(await profiles.card_of(session, profile, settings)),
            "bio": profile.bio,
            "skills": await profiles.skills_of(session, profile.id),
            "languages": await profiles.languages_of(session, profile.id),
            "availability": await profiles.availability_of(session, profile.id),
            "overlap_hours_per_day": overlap_minutes // 60 // 7,
            "reviews": await profiles.reviews_of(session, profile.id),
        }
    )


@router.get("/profiles/{profile_id}/trust")
async def profile_trust(profile_id: UUID, session: SessionDep, settings: SettingsDep):
    profile = await _get_profile(session, profile_id)
    projection = await profiles.trust_of(session, profile.id, settings)
    return ok(
        {
            "profile_id": str(profile.id),
            "status": projection.status,
            "value": projection.value,
            "is_demo": projection.is_demo,
            "policy_version": projection.policy_version,
        }
    )


@router.get("/catalog/skills")
async def skills_catalog(session: SessionDep, q: str = ""):
    query = select(Skill).order_by(Skill.display_name).limit(20)
    if q.strip():
        query = query.where(Skill.normalized_name.contains(q.strip().lower()))
    rows = (await session.execute(query)).scalars()
    return ok([{"name": row.display_name} for row in rows])
