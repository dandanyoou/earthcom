"""M1 request parser — extraction only (schema parse.v2, stub implementation).

The parser structures what the requester wrote. It never designs roles: the
roles array is a verbatim pass-through of the form rows, so an AI-invented
role is unrepresentable. Numbers that are not in the text stay null.
"""

import re
import unicodedata
from typing import Any

from pangaea_ai import lexicon

SCHEMA_VERSION = "parse.v2"

_WEEKS = re.compile(r"(\d{1,3})\s*주")
_MONTHS = re.compile(r"(\d{1,2})\s*개월")
_AMOUNT_MANWON = re.compile(r"(\d{1,6})\s*만\s*원")
_AMOUNT_WON = re.compile(r"(\d{1,3}(?:,\d{3})+|\d{4,9})\s*원")
_HANGUL = re.compile(r"[가-힣]")


def normalize_role_label(label: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", label).strip())


def role_multiset(roles: list[dict[str, Any]]) -> list[tuple[int, str, int | None]]:
    return sorted(
        (
            (
                int(role["form_position"]),
                normalize_role_label(str(role["label"])),
                role.get("headcount"),
            )
            for role in roles
        ),
    )


def _detect_language(text: str) -> str:
    hangul = len(_HANGUL.findall(text))
    return "ko" if hangul >= max(1, len(text) // 20) else "en"


def _detect_signal_type(lowered: str) -> str:
    for signal_type, keywords in lexicon.SIGNAL_TYPE_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return signal_type
    return "WORK"


def _detect_skills(text: str, lowered: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for canonical, aliases in lexicon.SKILL_ALIASES.items():
        for alias in aliases:
            index = lowered.find(alias)
            if index >= 0 and canonical not in seen:
                seen.add(canonical)
                found.append(
                    {
                        "name": canonical,
                        "origin": "EXPLICIT",
                        "evidence_span": text[index : index + len(alias)],
                        "importance": 0.5,  # uncertainty metadata only; discarded upstream
                    }
                )
                break
        if len(found) >= 8:
            break
    return found


def _detect_duration(text: str) -> dict[str, Any]:
    hedged = any(marker in text for marker in lexicon.HEDGE_MARKERS)
    match = _WEEKS.search(text)
    if match:
        return {
            "weeks": int(match.group(1)),
            "origin": "INFERRED" if hedged else "EXPLICIT",
            "evidence_span": match.group(0),
        }
    match = _MONTHS.search(text)
    if match:
        return {
            "weeks": int(match.group(1)) * 4,
            "origin": "INFERRED",
            "evidence_span": match.group(0),
        }
    return {"weeks": None, "origin": "DEFAULT", "evidence_span": None}


def _detect_compensation(text: str, lowered: str, signal_type: str) -> dict[str, Any]:
    if any(marker in lowered for marker in lexicon.UNPAID_MARKERS):
        return {
            "is_paid": False,
            "amount_krw": None,
            "currency": "NONE",
            "origin": "EXPLICIT",
            "evidence_span": next(m for m in lexicon.UNPAID_MARKERS if m in lowered),
        }
    match = _AMOUNT_MANWON.search(text)
    if match:
        return {
            "is_paid": True,
            "amount_krw": int(match.group(1)) * 10_000,
            "currency": "KRW",
            "origin": "EXPLICIT",
            "evidence_span": match.group(0),
        }
    match = _AMOUNT_WON.search(text)
    if match:
        return {
            "is_paid": True,
            "amount_krw": int(match.group(1).replace(",", "")),
            "currency": "KRW",
            "origin": "EXPLICIT",
            "evidence_span": match.group(0),
        }
    if signal_type in ("WORK", "BOOKING"):
        # Paid by definition, amount undecided — shown as a dashed "추정" tag.
        return {
            "is_paid": True,
            "amount_krw": None,
            "currency": "NONE",
            "origin": "INFERRED",
            "evidence_span": None,
        }
    return {
        "is_paid": False,
        "amount_krw": None,
        "currency": "NONE",
        "origin": "NONE",
        "evidence_span": None,
    }


def _detect_location(text: str, lowered: str) -> dict[str, Any]:
    requires_presence = any(marker in lowered for marker in lexicon.PHYSICAL_PRESENCE_KEYWORDS)
    area_hint = None
    for city in lexicon.CITY_NAMES:
        if city in text:
            area_hint = city
            break
    origin = "EXPLICIT" if (requires_presence or area_hint) else "NONE"
    return {
        "requires_physical_presence": requires_presence,
        "area_hint": area_hint,
        "origin": origin,
    }


def _detect_license_risk(lowered: str) -> dict[str, Any]:
    for keyword in lexicon.DERIVATIVE_IP_KEYWORDS:
        if keyword in lowered:
            return {
                "flagged": True,
                "kind": "DERIVATIVE_IP",
                "rationale": f"'{keyword}' 표현이 원작 IP 사용을 시사합니다.",
            }
    return {"flagged": False, "kind": "NONE", "rationale": None}


def _detect_credentials(lowered: str) -> list[str]:
    detected = [
        credential
        for credential, keywords in lexicon.CREDENTIAL_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    ]
    return detected[:5]


def parse(raw_text: str, roles_form: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic parse.v2 output. roles_form rows: {label, headcount, form_position}."""
    text = raw_text.strip()
    lowered = text.lower()
    signal_type = _detect_signal_type(lowered)

    urgency = "NORMAL"
    if any(k in lowered for k in lexicon.URGENCY_CRITICAL):
        urgency = "CRITICAL"
    elif any(k in lowered for k in lexicon.URGENCY_HIGH):
        urgency = "HIGH"
    if signal_type == "HELP" and ("새벽" in text or "병원" in text):
        urgency = "CRITICAL"

    roles_requested = [
        {
            "label": normalize_role_label(str(role["label"]))[:40],
            "origin": "EXPLICIT",
            "evidence_span": str(role["label"]),
            "headcount": role.get("headcount"),
            "form_position": int(role["form_position"]),
        }
        for role in roles_form[:8]
    ]

    headcount_hint = sum(r["headcount"] or 0 for r in roles_requested) or None
    cardinality = "1:1" if (headcount_hint == 1 and len(roles_requested) <= 1) else "1:N"
    target_is_team = any(marker in lowered for marker in lexicon.TEAM_TARGET_MARKERS)

    return {
        "signal_type": signal_type,
        "urgency": urgency,
        "roles_requested": roles_requested,
        "skills": _detect_skills(text, lowered),
        "duration": _detect_duration(text),
        "team_shape": {
            "cardinality": "N:N" if target_is_team else cardinality,
            "headcount_hint": headcount_hint,
            "target_is_team": target_is_team,
        },
        "compensation": _detect_compensation(text, lowered, signal_type),
        "deliverables": [],
        "location_requirement": _detect_location(text, lowered),
        "license_risk": _detect_license_risk(lowered),
        "required_credentials": _detect_credentials(lowered),
        "source_language": _detect_language(text),
        "confidence": 0.7,
        "unmapped_spans": [],
    }
