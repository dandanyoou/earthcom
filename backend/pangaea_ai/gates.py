"""Deterministic gates that sit between any AI output and the product.

Machine-verifiable things are verified by machines: numeral preservation,
stereotype phrasing, naked judgment numbers, and knowledge-base confidence
decay all live here as plain code.
"""

import re
from collections import Counter
from datetime import date

NUMERAL = re.compile(r"\d+(?:[.,]\d+)*")

# Statements about "all/every/always <people>" are banned; tendency markers are required.
STEREOTYPE_BANNED = [
    re.compile(r"(모든|전부|항상|원래|다)\s*\S*\s*(사람들|인들)은"),
    re.compile(r"\S+인은\s+\S+하다$"),
    re.compile(r"(절대|반드시)\s+\S+(한다|합니다)"),
]
TENDENCY_MARKERS = (
    "경우가 많",
    "경향이 있",
    "편입니다",
    "편이에요",
    "하는 편",
    "일반적으로",
    "자주",
    "많습니다",
    "경우가 있",
    "수 있어요",
)
RESERVATION_MARKERS = ("다를 수 있", "사람마다", "상대에 따라")

# Judgment-shaped tokens that AI-authored copy must never introduce (§2.2-3).
JUDGMENT_TOKENS = re.compile(r"[₩°%]|(\d+(?:[.,]\d+)*\s*(원|점|위))")
SLOT = re.compile(r"\{\{[^{}]+\}\}")


def numeral_multiset_ok(source: str, translated: str) -> bool:
    return Counter(NUMERAL.findall(source)) == Counter(NUMERAL.findall(translated))


def expansion_ok(source: str, translated: str, max_expansion: float) -> bool:
    return len(translated) <= len(source) * max_expansion + 40


def stereotype_lint_ok(annotation: str, *, require_reservation: bool = False) -> bool:
    if any(pattern.search(annotation) for pattern in STEREOTYPE_BANNED):
        return False
    if not any(marker in annotation for marker in TENDENCY_MARKERS):
        return False
    if require_reservation and not any(marker in annotation for marker in RESERVATION_MARKERS):
        return False
    return True


def no_naked_numbers_ok(text: str) -> bool:
    """AI-authored sentences may carry numbers only inside {{slots}}."""
    return not NUMERAL.search(SLOT.sub("", text)) and not JUDGMENT_TOKENS.search(SLOT.sub("", text))


HALFLIFE_DAYS, DISPUTE_PENALTY, CONF_FLOOR = 365, 0.05, 0.30


def effective_confidence(
    base_confidence: float, verified_at: date, dispute_count: int, *, today: date
) -> float:
    decayed = base_confidence * (0.5 ** ((today - verified_at).days / HALFLIFE_DAYS))
    return max(CONF_FLOOR, round(decayed - DISPUTE_PENALTY * dispute_count, 2))


def confidence_level(effective: float) -> str | None:
    """Three display bands: 강 ≥0.75 / 보통 0.65–0.75 / 참고 0.50–0.65."""
    if effective >= 0.75:
        return "STRONG"
    if effective >= 0.65:
        return "MODERATE"
    if effective >= 0.50:
        return "REFERENCE"
    return None


def fill_slots(template: str, values: dict[str, str]) -> str | None:
    """Deterministic slot substitution with Korean particle resolution.

    Returns None when an unknown slot remains after substitution — the caller
    must discard the sentence and fall back.
    """

    def josa(word: str, pair: str) -> str:
        first, second = pair.split("/")
        if not word:
            return second
        code = ord(word[-1])
        if 0xAC00 <= code <= 0xD7A3:
            return first if (code - 0xAC00) % 28 else second
        return second if word[-1].upper() in "AEIOUWY0123456789" else first

    def replace(match: re.Match[str]) -> str:
        inner = match.group(0)[2:-2]
        if ":" in inner:
            name, pair = inner.split(":", 1)
            if name not in values:
                return match.group(0)
            return values[name] + josa(values[name], pair)
        return values.get(inner, match.group(0))

    result = re.sub(r"\{\{[^{}]+\}\}", replace, template)
    return None if "{{" in result else result
