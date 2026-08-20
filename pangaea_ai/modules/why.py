"""M6 recommendation reasons — the AI never sees the numbers.

Templates carry slot names; the deterministic substitution happens here with
values the caller resolved from server facts. A sentence with a digit outside
a slot, or an unresolved slot, is discarded (§7.9).
"""

from typing import Any

from pangaea_ai import lexicon
from pangaea_ai.gates import fill_slots, no_naked_numbers_ok

SCHEMA_VERSION = "why.v2"

FALLBACK_SENTENCE = "요청 조건과 프로필이 겹쳐 추천드려요."


def compose(facts: dict[str, Any]) -> str:
    """facts: subset of {skill, years, overlap_hours, verified_count, city, lang}."""
    available = {key: str(value) for key, value in facts.items() if value not in (None, "", 0)}
    for template_spec in lexicon.WHY_TEMPLATES:
        if not all(required in available for required in template_spec["requires"]):
            continue
        template = template_spec["template"]
        if not no_naked_numbers_ok(template):
            continue  # a template with naked numbers is a bug — skip it defensively
        sentence = fill_slots(template, available)
        if sentence is not None:
            return sentence
    return FALLBACK_SENTENCE
