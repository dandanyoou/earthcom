"""Current user: profile, skills, languages, availability (S07)."""

import re
from datetime import time
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.models import Notification
from app.domains.profiles import service as profiles
from app.domains.profiles.models import (
    AvailabilityRule,
    Profile,
    ProfileLanguage,
    ProfileSkill,
    Skill,
)
from app.envelope import ok
from app.errors import ProductError
from app.platform.authz import Identity, get_identity
from app.platform.db import get_db_session
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1/me", tags=["me"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
IdentityDep = Annotated[Identity, Depends(get_identity)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


class ProfilePatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    bio: str | None = Field(default=None, max_length=2000)
    city_code: str | None = Field(default=None, max_length=32)
    timezone: str | None = Field(default=None, max_length=64)
    locale: str | None = Field(default=None, pattern="^[a-z]{2}$")


class SkillInput(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    years: int | None = Field(default=None, ge=0, le=60)


class LanguageInput(BaseModel):
    code: str = Field(pattern="^[a-z]{2}$")
    proficiency: str = Field(pattern="^(BASIC|CONVERSATIONAL|PROFESSIONAL|NATIVE)$")


class AvailabilityInput(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start: str = Field(pattern="^\\d{2}:\\d{2}$")
    end: str = Field(pattern="^\\d{2}:\\d{2}$")


def _require_profile(identity: Identity) -> Profile:
    if identity.profile is None:
        raise ProductError(code="PROFILE_NOT_ACTIVE", message="profile missing", status_code=422)
    return identity.profile


@router.get("")
async def me(session: SessionDep, identity: IdentityDep, settings: SettingsDep):
    unread = 0
    if identity.profile is not None:
        unread = (
            await session.execute(
                select(func.count())
                .select_from(Notification)
                .where(Notification.user_id == identity.user_id, Notification.read_at.is_(None))
            )
        ).scalar_one()
    return ok(
        {
            "user_id": str(identity.user_id),
            "email": identity.email,
            "locale": identity.locale,
            "unread_notifications": unread,
            "profile": (
                await profiles.card_of(session, identity.profile, settings)
                if identity.profile
                else None
            ),
        }
    )


@router.get("/profile")
async def my_profile(session: SessionDep, identity: IdentityDep, settings: SettingsDep):
    profile = _require_profile(identity)
    return ok(
        {
            **(await profiles.card_of(session, profile, settings)),
            "bio": profile.bio,
            "status": profile.status,
            "skills": await profiles.skills_of(session, profile.id),
            "languages": await profiles.languages_of(session, profile.id),
            "availability": await profiles.availability_of(session, profile.id),
        }
    )


@router.patch("/profile")
async def patch_profile(
    body: ProfilePatch, session: SessionDep, identity: IdentityDep, settings: SettingsDep
):
    profile = _require_profile(identity)
    for field in ("display_name", "bio", "city_code", "timezone", "locale"):
        value = getattr(body, field)
        if value is not None:
            setattr(profile, field, value)
    if profile.status == "DRAFT":
        profile.status = "ACTIVE"
    profile.version += 1
    await session.commit()
    return ok(await profiles.card_of(session, profile, settings))


def _normalize_skill(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).lower()


@router.put("/skills")
async def put_skills(body: list[SkillInput], session: SessionDep, identity: IdentityDep):
    profile = _require_profile(identity)
    await session.execute(delete(ProfileSkill).where(ProfileSkill.profile_id == profile.id))
    for item in body[:12]:
        normalized = _normalize_skill(item.name)
        skill = (
            await session.execute(select(Skill).where(Skill.normalized_name == normalized))
        ).scalar_one_or_none()
        if skill is None:
            skill = Skill(normalized_name=normalized, display_name=item.name.strip())
            session.add(skill)
            await session.flush()
        session.add(
            ProfileSkill(
                profile_id=profile.id,
                skill_id=skill.id,
                years_experience=item.years,
                verification_status="UNVERIFIED",
            )
        )
    await session.commit()
    return ok(await profiles.skills_of(session, profile.id))


@router.put("/languages")
async def put_languages(body: list[LanguageInput], session: SessionDep, identity: IdentityDep):
    profile = _require_profile(identity)
    await session.execute(delete(ProfileLanguage).where(ProfileLanguage.profile_id == profile.id))
    for item in body[:8]:
        session.add(
            ProfileLanguage(
                profile_id=profile.id,
                language_code=item.code,
                proficiency=item.proficiency,
            )
        )
    await session.commit()
    return ok(await profiles.languages_of(session, profile.id))


@router.put("/availability")
async def put_availability(
    body: list[AvailabilityInput], session: SessionDep, identity: IdentityDep
):
    profile = _require_profile(identity)
    await session.execute(delete(AvailabilityRule).where(AvailabilityRule.profile_id == profile.id))
    for position, item in enumerate(body[:14]):
        start_h, start_m = item.start.split(":")
        end_h, end_m = item.end.split(":")
        local_start = time(int(start_h), int(start_m))
        local_end = time(int(end_h), int(end_m))
        if local_start >= local_end:
            raise ProductError(
                code="AVAILABILITY_INVALID",
                message="start must be before end",
                status_code=422,
            )
        session.add(
            AvailabilityRule(
                profile_id=profile.id,
                weekday=item.weekday,
                local_start=local_start,
                local_end=local_end,
                timezone=profile.timezone,
                rule_position=position,
            )
        )
    await session.commit()
    return ok(await profiles.availability_of(session, profile.id))
