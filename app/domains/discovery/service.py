"""Recommendations and direct search — deterministic ordering, AI never ranks.

The AI contributes two expression-only pieces: M8 widens search terms and M6
phrases the reason sentence from server facts. Order always comes from
matching.v1; culture, nationality, trust, and AI confidence are not inputs.
"""

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profiles import service as profiles
from app.domains.profiles.models import Profile
from app.domains.signals.models import Signal, SignalRole, SignalSkill
from app.platform.overlap import weekly_overlap_minutes
from app.policies.matching import EXPLAIN_KEYS, POLICY_VERSION, CandidateFeatures, order
from app.settings import Settings
from pangaea_ai.modules import search as m8
from pangaea_ai.modules import why as m6

_TOKEN = re.compile(r"[A-Za-z0-9가-힣]+")


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN.findall(text) if len(token) > 1}


async def _candidate_pool(
    session: AsyncSession, *, target_is_team: bool, exclude_profile_id
) -> list[Profile]:
    query = select(Profile).where(
        Profile.status == "ACTIVE",
        Profile.kind == ("TEAM" if target_is_team else "PERSON"),
        Profile.id != exclude_profile_id,
    )
    return list((await session.execute(query)).scalars())


async def _profile_features(
    session: AsyncSession,
    profile: Profile,
    *,
    wanted_skills: set[str],
    role_tokens: set[str],
    source_language: str,
    requester_rules: list[tuple],
) -> CandidateFeatures:
    skills = await profiles.skills_of(session, profile.id)
    skill_names = {skill["normalized"] for skill in skills}
    skill_tokens = set().union(*(_tokens(skill["name"]) for skill in skills)) if skills else set()
    languages = await profiles.languages_of(session, profile.id)
    language_match = int(
        any(
            lang["code"] == source_language and lang["proficiency"] in ("PROFESSIONAL", "NATIVE")
            for lang in languages
        )
    )
    overlap = weekly_overlap_minutes(
        requester_rules, await profiles.availability_rules_of(session, profile.id)
    )
    verified_relevant = sum(
        1 for skill in skills if skill["verified"] and skill["normalized"] in wanted_skills
    )
    return CandidateFeatures(
        profile_id=profile.id,
        required_skill_exact_match_count=len(wanted_skills & skill_names),
        requested_role_label_token_match_count=len(role_tokens & skill_tokens),
        professional_or_native_language_match=language_match,
        weekly_overlap_minutes=overlap,
        verified_relevant_portfolio_count=verified_relevant,
        extras={"profile": profile, "skills": skills},
    )


def explain_panel() -> dict:
    """Server-owned copy of the ordering rules (§4.6-B) — never hardcoded client-side."""
    return {
        "policy_version": POLICY_VERSION,
        "criteria": list(EXPLAIN_KEYS),
        "exclusions": ["cultureExcluded", "trustExcluded"],
    }


async def recommend(
    session: AsyncSession, signal: Signal, settings: Settings, *, limit: int = 10
) -> dict:
    wanted_skills = {
        row.skill_name.lower()
        for row in (
            await session.execute(select(SignalSkill).where(SignalSkill.signal_id == signal.id))
        ).scalars()
    }
    role_tokens: set[str] = set()
    for role in (
        await session.execute(select(SignalRole).where(SignalRole.signal_id == signal.id))
    ).scalars():
        role_tokens |= _tokens(role.label)

    requester_rules = await profiles.availability_rules_of(session, signal.requester_profile_id)
    pool = await _candidate_pool(
        session,
        target_is_team=signal.target_is_team,
        exclude_profile_id=signal.requester_profile_id,
    )
    features = [
        await _profile_features(
            session,
            profile,
            wanted_skills=wanted_skills,
            role_tokens=role_tokens,
            source_language=signal.source_language,
            requester_rules=requester_rules,
        )
        for profile in pool
    ]
    ordered = order(features)[:limit]

    candidates = []
    for rank, candidate in enumerate(ordered, start=1):
        profile = candidate.extras["profile"]
        card = await profiles.card_of(session, profile, settings)
        matched_skill = None
        for skill in candidate.extras["skills"]:
            if skill["normalized"] in wanted_skills:
                matched_skill = skill
                break
        facts = {
            "skill": (matched_skill or (candidate.extras["skills"] or [{}])[0]).get("name"),
            "years": (matched_skill or {}).get("years"),
            "overlap_hours": candidate.weekly_overlap_minutes // 60 // 7 or None,
            "verified_count": candidate.verified_relevant_portfolio_count or None,
        }
        role_fit = (
            "MATCHED"
            if (
                candidate.required_skill_exact_match_count > 0
                or candidate.requested_role_label_token_match_count > 0
            )
            else "DIFFERENT"
        )
        candidates.append(
            {
                "rank": rank,
                "profile": card,
                "role_fit": role_fit,
                "overlap_hours_per_day": candidate.weekly_overlap_minutes // 60 // 7,
                "verified_relevant_count": candidate.verified_relevant_portfolio_count,
                "why": m6.compose(facts) if role_fit == "MATCHED" else None,
            }
        )
    return {"explain": explain_panel(), "candidates": candidates}


async def search_profiles(
    session: AsyncSession, query: str, settings: Settings, *, limit: int = 30
) -> dict:
    normalized = m8.normalize(query)
    terms = {term.lower() for term in normalized["terms"]}
    query_language = "ko" if re.search(r"[가-힣]", query) else "en"

    pool = list(
        (
            await session.execute(
                select(Profile).where(Profile.status == "ACTIVE", Profile.kind == "PERSON")
            )
        ).scalars()
    )
    features = []
    for profile in pool:
        skills = await profiles.skills_of(session, profile.id)
        haystack = {skill["normalized"] for skill in skills}
        haystack |= _tokens(profile.display_name)
        if profile.city_code:
            haystack.add(profile.city_code.lower())
        matched_terms = {term for term in terms if term in haystack}
        if terms and not matched_terms:
            continue
        languages = await profiles.languages_of(session, profile.id)
        language_match = int(
            any(
                lang["code"] == query_language and lang["proficiency"] in ("PROFESSIONAL", "NATIVE")
                for lang in languages
            )
        )
        features.append(
            CandidateFeatures(
                profile_id=profile.id,
                required_skill_exact_match_count=len(matched_terms & haystack),
                requested_role_label_token_match_count=0,
                professional_or_native_language_match=language_match,
                weekly_overlap_minutes=0,
                verified_relevant_portfolio_count=sum(1 for s in skills if s["verified"]),
                search_term_match_count=len(matched_terms),
                extras={"profile": profile},
            )
        )
    ordered = order(features, include_search_terms=True)[:limit]
    results = [
        await profiles.card_of(session, candidate.extras["profile"], settings)
        for candidate in ordered
    ]
    return {"terms": normalized["terms"], "results": results, "total": len(features)}
