"""Profile reads shared by every screen: cards, trust projection, details."""

from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profiles.models import (
    AvailabilityRule,
    Profile,
    ProfileLanguage,
    ProfileSkill,
    Skill,
)
from app.domains.reputation.models import Review, TrustEvent
from app.policies import trust
from app.settings import Settings


def initials_of(display_name: str) -> str:
    parts = [part for part in display_name.replace(".", " ").split() if part]
    if not parts:
        return "?"
    if any("가" <= ch <= "힣" for ch in display_name):
        compact = display_name.replace(" ", "")
        return compact[:2]
    letters = [part[0].upper() for part in parts[:2]]
    return "".join(letters)


def palette_of(profile_id: UUID) -> int:
    return (profile_id.int % 6) + 1


def local_time_of(timezone_name: str, at: datetime | None = None) -> str:
    moment = at or datetime.now(UTC)
    try:
        return moment.astimezone(ZoneInfo(timezone_name)).strftime("%H:%M")
    except KeyError:
        return moment.strftime("%H:%M")


async def trust_of(
    session: AsyncSession, profile_id: UUID, settings: Settings
) -> trust.TrustProjection:
    rows = (
        await session.execute(
            select(TrustEvent.event_key, TrustEvent.demo_delta)
            .where(TrustEvent.profile_id == profile_id)
            .order_by(TrustEvent.created_at)
        )
    ).all()
    events = [
        trust.TrustEventInput(key, float(delta) if delta is not None else None)
        for key, delta in rows
    ]
    return trust.project(events, policy_version=settings.trust_policy_version)


async def skills_of(session: AsyncSession, profile_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            select(Skill.display_name, Skill.normalized_name, ProfileSkill)
            .join(ProfileSkill, ProfileSkill.skill_id == Skill.id)
            .where(ProfileSkill.profile_id == profile_id)
            .order_by(ProfileSkill.created_at)
        )
    ).all()
    return [
        {
            "name": display_name,
            "normalized": normalized,
            "years": link.years_experience,
            "verified": link.verification_status == "VERIFIED",
        }
        for display_name, normalized, link in rows
    ]


async def languages_of(session: AsyncSession, profile_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            select(ProfileLanguage)
            .where(ProfileLanguage.profile_id == profile_id)
            .order_by(ProfileLanguage.created_at)
        )
    ).scalars()
    return [{"code": row.language_code, "proficiency": row.proficiency} for row in rows]


async def availability_of(session: AsyncSession, profile_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            select(AvailabilityRule)
            .where(AvailabilityRule.profile_id == profile_id)
            .order_by(AvailabilityRule.rule_position)
        )
    ).scalars()
    return [
        {
            "weekday": row.weekday,
            "start": row.local_start.strftime("%H:%M"),
            "end": row.local_end.strftime("%H:%M"),
            "timezone": row.timezone,
        }
        for row in rows
    ]


async def availability_rules_of(session: AsyncSession, profile_id: UUID) -> list[tuple]:
    rows = (
        await session.execute(
            select(AvailabilityRule).where(AvailabilityRule.profile_id == profile_id)
        )
    ).scalars()
    return [(row.weekday, row.local_start, row.local_end, row.timezone) for row in rows]


async def card_of(
    session: AsyncSession, profile: Profile, settings: Settings, *, with_trust: bool = True
) -> dict:
    skills = await skills_of(session, profile.id)
    headline_parts: list[str] = []
    for skill in skills[:2]:
        if skill["years"]:
            headline_parts.append(f"{skill['name']} {skill['years']}년")
        else:
            headline_parts.append(skill["name"])
    card = {
        "id": str(profile.id),
        "display_name": profile.display_name,
        "initials": initials_of(profile.display_name),
        "palette": palette_of(profile.id),
        "kind": profile.kind,
        "locale": profile.locale,
        "timezone": profile.timezone,
        "city_code": profile.city_code,
        "local_time": local_time_of(profile.timezone),
        "headline": " · ".join(headline_parts),
        "verified_count": sum(1 for skill in skills if skill["verified"]),
    }
    if with_trust:
        projection = await trust_of(session, profile.id, settings)
        card["trust"] = {
            "value": projection.value,
            "status": projection.status,
            "is_demo": projection.is_demo,
        }
    return card


async def reviews_of(session: AsyncSession, profile_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            select(Review, Profile.display_name)
            .join(Profile, Profile.id == Review.reviewer_profile_id)
            .where(Review.reviewee_profile_id == profile_id)
            .order_by(Review.created_at.desc())
            .limit(20)
        )
    ).all()
    return [
        {
            "id": str(review.id),
            "rating": review.rating,
            "tags": review.tags,
            "comment": review.comment,
            "reviewer_name": reviewer_name,
            "created_at": review.created_at.isoformat(),
        }
        for review, reviewer_name in rows
    ]


async def city_counts(session: AsyncSession) -> dict[str, int]:
    rows = (
        await session.execute(
            select(Profile.city_code, func.count())
            .where(Profile.status == "ACTIVE", Profile.city_code.is_not(None))
            .group_by(Profile.city_code)
        )
    ).all()
    return {city: count for city, count in rows}
