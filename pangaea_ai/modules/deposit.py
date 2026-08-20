"""M7 deposit copy — clause keys map 1:1 to the rule engine's output.

Whether a clause appears is decided by deterministic rules, never by a model.
Amounts and caps appear only as slots the caller fills after the fact, and the
work-payment notice is mandatory (§7.10).
"""

from pangaea_ai import lexicon
from pangaea_ai.gates import fill_slots

SCHEMA_VERSION = "deposit.v1"


def draft(clause_keys: list[str], slot_values: dict[str, str]) -> dict[str, object]:
    clauses: list[dict[str, str]] = []
    for key in clause_keys:
        template = lexicon.DEPOSIT_CLAUSES.get(key)
        if template is None:
            continue
        text = fill_slots(template, slot_values)
        if text is None:
            continue
        clauses.append({"key": key, "text": text})
    return {"clauses": clauses, "notice": lexicon.DEPOSIT_NOTICE}
