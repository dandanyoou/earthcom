from uuid import UUID

from app.policies.matching import CandidateFeatures, order
from app.policies.trust import TrustEventInput, project


def test_trust_completion_reproduces_demo_values() -> None:
    # 37.3 → 38.5 and 41.2 → 42.4 from the mockup: one completion is +1.2.
    seeded = [TrustEventInput("DEMO_SEED", 0.8)]
    assert project(seeded).value == 37.3
    assert project([*seeded, TrustEventInput("COLLABORATION_COMPLETED")]).value == 38.5

    weber = [TrustEventInput("DEMO_SEED", 4.7)]
    assert project(weber).value == 41.2
    assert project([*weber, TrustEventInput("COLLABORATION_COMPLETED")]).value == 42.4


def test_trust_is_deterministic_and_clamped() -> None:
    events = [TrustEventInput("NO_SHOW_CONFIRMED")] * 10
    first = project(events)
    assert first.value == 30.0
    assert project(events) == first
    assert project([TrustEventInput("COLLABORATION_COMPLETED")] * 50).value == 50.0


def test_trust_disabled_returns_unavailable() -> None:
    projection = project([TrustEventInput("COLLABORATION_COMPLETED")], policy_version="disabled")
    assert projection.status == "UNAVAILABLE"
    assert projection.value is None


def test_matching_order_is_lexicographic_not_weighted() -> None:
    strong_skill = CandidateFeatures(
        profile_id=UUID(int=2),
        required_skill_exact_match_count=2,
        requested_role_label_token_match_count=0,
        professional_or_native_language_match=0,
        weekly_overlap_minutes=0,
        verified_relevant_portfolio_count=0,
    )
    # Massive later-key values must never beat an earlier key.
    everything_else = CandidateFeatures(
        profile_id=UUID(int=1),
        required_skill_exact_match_count=1,
        requested_role_label_token_match_count=99,
        professional_or_native_language_match=1,
        weekly_overlap_minutes=10_000,
        verified_relevant_portfolio_count=99,
    )
    assert order([everything_else, strong_skill])[0] is strong_skill


def test_matching_tie_breaks_on_profile_id_ascending() -> None:
    def candidate(index: int) -> CandidateFeatures:
        return CandidateFeatures(
            profile_id=UUID(int=index),
            required_skill_exact_match_count=1,
            requested_role_label_token_match_count=1,
            professional_or_native_language_match=1,
            weekly_overlap_minutes=60,
            verified_relevant_portfolio_count=1,
        )

    ordered = order([candidate(9), candidate(3)])
    assert [c.profile_id for c in ordered] == [UUID(int=3), UUID(int=9)]
