"""M3 pre-send guard — warns, never blocks (schema guard.v2, stub implementation).

Display rule (§7.6): risk ∈ {MEDIUM, HIGH} — or LOW for taboo phenomena —
AND confidence ≥ threshold AND real KB evidence AND a concrete suggestion.
A warning without an alternative only freezes people, so suggestion is required.
"""

import hashlib
import re
from typing import Any

from pangaea_ai import lexicon

SCHEMA_VERSION = "guard.v2"

_NONE_RESULT: dict[str, Any] = {
    "rewritten_text": None,
    "risk": "NONE",
    "phenomenon": "NONE",
    "reader_reading": None,
    "suggestion": None,
    "kb_ids": [],
    "confidence": 1.0,
    "direction": None,
    "display": False,
}


def _apply_rewrite(text: str, spec) -> str | None:
    """Deterministic concrete rewrite; None when only advice is possible."""
    if spec is None:
        return None
    kind, *args = spec
    if kind == "regex":
        pattern, replacement = args
        rewritten = re.sub(pattern, replacement, text)
    else:
        rewritten = text
        for source, target in args[0].items():
            rewritten = rewritten.replace(source, target)
    return rewritten if rewritten != text else None


def input_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def evaluate(
    text: str,
    *,
    source_lang: str,
    target_langs: list[str],
    known_kb_ids: set[str],
    min_confidence: float = 0.70,
) -> dict[str, Any]:
    """Returns the highest-risk matching rule for the recipients' language spheres."""
    matches: list[tuple[int, dict, str]] = []
    risk_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    for rule in lexicon.GUARD_RULES:
        applicable_targets = [t for t in target_langs if t in rule["target_langs"]]
        if not applicable_targets:
            continue
        if not re.search(rule["regex"], text):
            continue
        matches.append((risk_order[rule["risk"]], rule, applicable_targets[0]))

    if not matches:
        return {**_NONE_RESULT, "direction": None}

    _, rule, target = max(matches, key=lambda item: item[0])
    rewritten = _apply_rewrite(text, rule.get("rewrite"))
    kb_ids = [kb_id for kb_id in rule["kb_ids"] if kb_id in known_kb_ids]
    taboo = rule["phenomenon"].startswith("TABOO")
    displayable = (
        (rule["risk"] in ("MEDIUM", "HIGH") or (rule["risk"] == "LOW" and taboo))
        and rule["confidence"] >= min_confidence
        and bool(kb_ids)
        and bool(rule["suggestion"])
    )
    return {
        "rewritten_text": rewritten,
        "risk": rule["risk"],
        "phenomenon": rule["phenomenon"],
        "reader_reading": rule["reader_reading"],
        "suggestion": rule["suggestion"],
        "kb_ids": kb_ids,
        "confidence": rule["confidence"],
        "direction": f"{source_lang}->{target}",
        "display": displayable,
    }
