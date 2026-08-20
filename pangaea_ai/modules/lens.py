"""M2 culture lens — L1 literal always, L3 intent only with cited evidence.

The asymmetry is the whole point (§7.5): a literal reading is always shown,
while a cultural annotation renders only when a real, sufficiently confident
KB record backs it. No evidence → silence, and silence is not an error.
"""

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from pangaea_ai import lexicon
from pangaea_ai.gates import confidence_level, effective_confidence, stereotype_lint_ok

SCHEMA_VERSION = "lens.v2"


@dataclass(frozen=True)
class KbRecord:
    id: str
    claim: str
    scope_locale: str
    scope_context: str
    confidence: float
    verified_at: date
    dispute_count: int


def annotate(
    *,
    source_text: str,
    source_lang: str,
    literal: str,
    kb_records: dict[str, KbRecord],
    today: date,
    min_confidence: float = 0.50,
) -> dict[str, Any]:
    """Returns {l1_literal, l3:{annotation, heading, level, kb_ids} | None}."""
    l3: dict[str, Any] | None = None
    for trigger in lexicon.LENS_TRIGGERS:
        if source_lang not in trigger["source_langs"]:
            continue
        if not re.search(trigger["regex"], source_text) and not re.search(
            trigger["regex"], literal
        ):
            continue
        record = kb_records.get(trigger["kb_id"])
        if record is None:  # nonexistent KB id — treat as hallucination, publish nothing
            continue
        effective = effective_confidence(
            record.confidence, record.verified_at, record.dispute_count, today=today
        )
        if effective < min_confidence:
            continue
        annotation = trigger["annotation"]
        if not stereotype_lint_ok(annotation):
            continue
        level = confidence_level(effective)
        if level is None:
            continue
        l3 = {
            "annotation": annotation,
            "heading": trigger["heading"],
            "level": level,
            "kb_ids": [record.id],
            "effective_confidence": effective,
        }
        break
    return {"l1_literal": literal, "l3": l3}
