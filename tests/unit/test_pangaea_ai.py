from datetime import date

import pytest

from pangaea_ai.gates import (
    effective_confidence,
    fill_slots,
    no_naked_numbers_ok,
    numeral_multiset_ok,
    stereotype_lint_ok,
)
from pangaea_ai.moderation import check as moderation_check
from pangaea_ai.modules import deposit, guard, lens, parse, search, why
from pangaea_ai.modules.translate import translate

EVA_TEXT = (
    "에반게리온 팬게임 같이 만들 사람 찾아요. 6주 정도 보고 있고, "
    "유니티 다루는 분과 캐릭터 아트 해주실 분이 필요해요."
)
EVA_ROLES = [
    {"label": "기획 · 디렉팅", "headcount": 1, "form_position": 0},
    {"label": "클라이언트 개발", "headcount": 1, "form_position": 1},
    {"label": "캐릭터 아트", "headcount": 1, "form_position": 2},
]


# ── M1 parser ────────────────────────────────────────────────────────────────
def test_parse_eva_fangame_matches_demo() -> None:
    result = parse.parse(EVA_TEXT, EVA_ROLES)
    assert result["signal_type"] == "WORK"
    assert {s["name"] for s in result["skills"]} >= {"Unity", "캐릭터 아트"}
    assert result["duration"] == {"weeks": 6, "origin": "INFERRED", "evidence_span": "6주"}
    assert result["compensation"]["origin"] == "INFERRED"  # 협의 — dashed tag
    assert result["compensation"]["amount_krw"] is None
    assert result["license_risk"] == {
        "flagged": True,
        "kind": "DERIVATIVE_IP",
        "rationale": "'팬게임' 표현이 원작 IP 사용을 시사합니다.",
    }


def test_parse_roles_are_verbatim_form_passthrough() -> None:
    # A fourth role is implied in the text but must never be added (B03/P09).
    text = EVA_TEXT + " 사운드 만들 분도 있으면 좋고요."
    result = parse.parse(text, EVA_ROLES)
    assert len(result["roles_requested"]) == 3
    assert parse.role_multiset(result["roles_requested"]) == parse.role_multiset(EVA_ROLES)
    assert all(role["origin"] == "EXPLICIT" for role in result["roles_requested"])


def test_parse_empty_role_form_yields_empty_roles() -> None:
    assert parse.parse(EVA_TEXT, [])["roles_requested"] == []


def test_parse_missing_numbers_stay_null() -> None:
    result = parse.parse("리액트 화면 손봐줄 분 구해요.", [])
    assert result["duration"]["weeks"] is None
    assert result["compensation"]["amount_krw"] is None


def test_parse_kabul_help_is_critical_with_medical_credential() -> None:
    result = parse.parse("새벽인데 아이 열이 39도예요. 카불에서 병원 좀 찾아주세요.", [])
    assert result["signal_type"] == "HELP"
    assert result["urgency"] == "CRITICAL"
    assert result["required_credentials"] == ["MEDICAL_LICENSE"]


# ── gates ────────────────────────────────────────────────────────────────────
def test_numeral_multiset_catches_changed_numbers() -> None:
    assert numeral_multiset_ok("3주 안에 2번", "within 3 weeks, 2 times")
    assert not numeral_multiset_ok("금요일까지 3주", "by Friday, 3 months and 2 days")


def test_stereotype_lint_requires_tendency_and_bans_absolutes() -> None:
    assert stereotype_lint_ok("직설적으로 말하는 편이에요.")
    assert not stereotype_lint_ok("모든 독일 사람들은 직설적이다")
    assert not stereotype_lint_ok("독일에서는 직설적으로 말한다")  # no tendency marker


def test_no_naked_numbers_allows_slots_only() -> None:
    assert no_naked_numbers_ok("{{skill}} 경력 {{years}}년이에요.")
    assert not no_naked_numbers_ok("Unity 경력 8년이에요.")
    assert not no_naked_numbers_ok("신뢰 온도 41.2°인 분이에요.")


def test_effective_confidence_matches_golden_de014() -> None:
    # DE-014: base 0.74, verified 2026-08-05, 3 disputes → 0.58 on 2026-08-12.
    assert effective_confidence(0.74, date(2026, 8, 5), 3, today=date(2026, 8, 12)) == 0.58


def test_fill_slots_resolves_korean_particles() -> None:
    assert fill_slots("{{skill:이/가}} 좋아요", {"skill": "셰이더"}) == "셰이더가 좋아요"
    assert fill_slots("{{skill:이/가}} 좋아요", {"skill": "디자인"}) == "디자인이 좋아요"
    assert fill_slots("{{missing}} 값", {}) is None


# ── M3 guard ─────────────────────────────────────────────────────────────────
KNOWN_KB = {"JP-011", "KO-012", "KO-001", "DE-021", "DE-031"}


def test_guard_flags_sato_ssi_for_japanese_recipient() -> None:
    result = guard.evaluate(
        "Sato씨, 캐릭터 시트 초안 봤어요!",
        source_lang="ko",
        target_langs=["ja", "de"],
        known_kb_ids=KNOWN_KB,
    )
    assert result["phenomenon"] == "HONORIFIC_MISMATCH"
    assert result["risk"] == "HIGH"
    assert result["display"] is True
    assert result["kb_ids"] == ["JP-011"]


def test_guard_rewrites_are_concrete_or_absent() -> None:
    honorific = guard.evaluate(
        "Sato씨, 시트 봤어요!", source_lang="ko", target_langs=["ja"], known_kb_ids=KNOWN_KB
    )
    assert honorific["rewritten_text"] == "Satoさん, 시트 봤어요!"
    slang = guard.evaluate(
        "그 부분 ㄱㄱ 하시면 될 듯요", source_lang="ko", target_langs=["de"], known_kb_ids=KNOWN_KB
    )
    assert slang["rewritten_text"] == "그 부분 진행 하시면 될 듯요"
    hold = guard.evaluate(
        "검토해 보겠습니다", source_lang="ko", target_langs=["de"], known_kb_ids=KNOWN_KB
    )
    assert hold["rewritten_text"] is None  # advice only — the UI hides the rewrite button


def test_guard_stays_silent_on_plain_text() -> None:
    result = guard.evaluate(
        "다음 회의는 목요일에 해요.",
        source_lang="ko",
        target_langs=["ja"],
        known_kb_ids=KNOWN_KB,
    )
    assert result["risk"] == "NONE"
    assert result["display"] is False


def test_guard_without_kb_evidence_does_not_display() -> None:
    result = guard.evaluate(
        "Sato씨, 보셨나요?",
        source_lang="ko",
        target_langs=["ja"],
        known_kb_ids=set(),  # KB missing → warn nothing
    )
    assert result["display"] is False


def test_guard_taboo_shows_even_at_low_risk_with_reservation() -> None:
    result = guard.evaluate(
        "실례지만 나이가 어떻게 되세요?",
        source_lang="ko",
        target_langs=["de"],
        known_kb_ids=KNOWN_KB,
    )
    assert result["risk"] == "LOW"
    assert result["display"] is True
    assert "다를 수 있어요" in result["suggestion"]


# ── M4 translation ───────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_translate_fixture_roundtrip() -> None:
    result = await translate(
        "상태 관리는 금요일까지 검토해서 알려드릴게요.",
        source_lang="ko",
        target_lang="de",
        provider="stub",
    )
    assert result.status == "READY"
    assert result.translated == "Ich schaue mir das State-Management an und melde mich bis Freitag."


@pytest.mark.asyncio
async def test_translate_unknown_text_fails_safe_to_original() -> None:
    result = await translate(
        "그 부분 ㄱㄱ 하시면 될 듯요",
        source_lang="ko",
        target_lang="de",
        provider="stub",
    )
    assert result.status == "UNSAFE_OR_FAILED"
    assert result.translated is None  # caller ships the original + review chip


@pytest.mark.asyncio
async def test_translate_same_language_passthrough() -> None:
    result = await translate("안녕하세요", source_lang="ko", target_lang="ko", provider="stub")
    assert result.status == "READY"
    assert result.translated == "안녕하세요"


# ── M2 lens ──────────────────────────────────────────────────────────────────
TODAY = date(2026, 8, 18)
KB_RECORDS = {
    "DE-014": lens.KbRecord(
        id="DE-014",
        claim="직설적 지적은 사안 중심인 경우가 많다",
        scope_locale="de",
        scope_context="업무 피드백",
        confidence=0.74,
        verified_at=date(2026, 8, 5),
        dispute_count=0,
    ),
    "JP-007": lens.KbRecord(
        id="JP-007",
        claim="정중한 보류가 거절로 기능하는 경우가 많다",
        scope_locale="ja",
        scope_context="의사 표현",
        confidence=0.78,
        verified_at=date(2026, 8, 5),
        dispute_count=0,
    ),
}


def test_lens_publishes_annotation_with_evidence() -> None:
    result = lens.annotate(
        source_text="Dieses State-Layer-Design skaliert nicht.",
        source_lang="de",
        literal="이 상태 관리 구조는 확장이 안 됩니다. 다시 만드는 게 맞습니다.",
        kb_records=KB_RECORDS,
        today=TODAY,
    )
    assert result["l3"] is not None
    assert result["l3"]["kb_ids"] == ["DE-014"]
    assert result["l3"]["heading"] == "READ_AS"


def test_lens_without_kb_record_stays_silent() -> None:
    result = lens.annotate(
        source_text="Dieses State-Layer-Design skaliert nicht.",
        source_lang="de",
        literal="이 상태 관리 구조는 확장이 안 됩니다.",
        kb_records={},  # sphere not covered → L1 only (the Kabul case)
        today=TODAY,
    )
    assert result["l3"] is None
    assert result["l1_literal"]


# ── M6 / M7 / M8 ─────────────────────────────────────────────────────────────
def test_why_substitutes_slots_deterministically() -> None:
    sentence = why.compose({"skill": "Unity", "years": 8})
    assert sentence == "Unity 경력 8년이라 찾으시는 기술과 바로 이어져요."


def test_why_falls_back_without_facts() -> None:
    assert why.compose({}) == why.FALLBACK_SENTENCE


def test_deposit_draft_has_notice_and_slot_amounts() -> None:
    result = deposit.draft(["DEPOSIT", "DERIVATIVE_IP"], {"amount": "100,000원"})
    assert result["notice"].startswith("보증금은 작업 대금이 아닙니다")
    assert result["clauses"][0]["text"].startswith("참여자 전원이 약속 보증금 100,000원")
    assert {c["key"] for c in result["clauses"]} == {"DEPOSIT", "DERIVATIVE_IP"}


def test_search_normalize_expands_synonyms_without_rank_fields() -> None:
    result = search.normalize("유니티 셰이더 잘하는 사람")
    assert "unity" in [t.lower() for t in result["terms"]]
    assert "shader" in [t.lower() for t in result["terms"]]
    assert set(result.keys()) == {"terms"}  # no boost/weight/sort_order/results


def test_moderation_self_harm_branch() -> None:
    assert moderation_check("요즘 죽고 싶다는 생각이 들어요") == "SELF_HARM_ROUTE"
    assert moderation_check("오늘 빌드 공유할게요") == "ALLOWED"
