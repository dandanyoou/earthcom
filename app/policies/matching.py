"""matching.v1 — deterministic candidate ordering.

No weighted sum: hard filters first, then a lexicographic sort tuple.
Culture distance, nationality, AI confidence, trust temperature, and deposit
amounts are deliberately absent from the tuple (§1.5-B/C). `rank` is the
position in this ordering, never an AI output.
"""

from dataclasses import dataclass, field
from uuid import UUID

POLICY_VERSION = "matching.v1"

# Rendered by the client inside the "how is this ordered?" fold, straight from
# the server so the screen can never drift from what the code actually does.
EXPLAIN_KEYS: tuple[str, ...] = (
    "skillMatch",
    "roleTokenMatch",
    "languageMatch",
    "overlapMinutes",
    "verifiedWork",
)


@dataclass(frozen=True)
class CandidateFeatures:
    profile_id: UUID
    required_skill_exact_match_count: int
    requested_role_label_token_match_count: int
    professional_or_native_language_match: int  # 0 or 1
    weekly_overlap_minutes: int
    verified_relevant_portfolio_count: int
    search_term_match_count: int = 0
    extras: dict = field(default_factory=dict)


def sort_key(candidate: CandidateFeatures, *, include_search_terms: bool = False):
    key = (
        -candidate.required_skill_exact_match_count,
        -candidate.requested_role_label_token_match_count,
        -candidate.professional_or_native_language_match,
        -candidate.weekly_overlap_minutes,
        -candidate.verified_relevant_portfolio_count,
        str(candidate.profile_id),
    )
    if include_search_terms:
        return (-candidate.search_term_match_count, *key)
    return key


def order(
    candidates: list[CandidateFeatures], *, include_search_terms: bool = False
) -> list[CandidateFeatures]:
    return sorted(candidates, key=lambda c: sort_key(c, include_search_terms=include_search_terms))
