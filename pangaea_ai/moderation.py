"""Deterministic moderation pre-processing.

Self-harm signals never enter any AI pipeline (§9.5): the caller branches to a
constant, locale-fixed crisis notice instead. Medical/legal disclaimers are
constants too — no runtime model generation path exists for them.
"""

from pangaea_ai import lexicon

CRISIS_NOTICE = {
    "ko": (
        "혼자 견디지 않으셔도 돼요. 지금 바로 자살예방 상담전화 109 "
        "또는 현지 응급번호로 연락해 주세요."
    ),
    "en": (
        "You do not have to face this alone. "
        "Please contact a local crisis line or emergency number right now."
    ),
}


def check(text: str) -> str:
    """Returns ALLOWED | SELF_HARM_ROUTE."""
    lowered = text.lower()
    if any(marker in lowered for marker in lexicon.SELF_HARM_MARKERS):
        return "SELF_HARM_ROUTE"
    return "ALLOWED"


def disclaimers_for(required_credentials: list[str], signal_type: str, urgency: str) -> list[str]:
    notes: list[str] = []
    if "MEDICAL_LICENSE" in required_credentials or (
        signal_type == "HELP" and urgency == "CRITICAL"
    ):
        notes.append(lexicon.DISCLAIMERS["MEDICAL"])
    if "LEGAL_LICENSE" in required_credentials:
        notes.append(lexicon.DISCLAIMERS["LEGAL"])
    return notes
