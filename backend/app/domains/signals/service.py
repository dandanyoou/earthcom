"""Signal lifecycle: deterministic parse adoption, the role contract, publish gate.

The server re-runs the parser itself and stores roles only from the form rows.
If the parse result's role multiset ever disagrees with the form, the parse is
discarded for roles and the form is copied verbatim (§6.5) — in the stub
parser they are identical by construction, but the check still runs.
"""

import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profiles.models import Profile
from app.domains.signals.models import Signal, SignalRole, SignalSkill
from app.errors import ProductError
from pangaea_ai import moderation
from pangaea_ai.modules import parse as m1

PII_PATTERNS = (
    re.compile(r"(?<!\d)01[016789]-?\d{3,4}-?\d{4}(?!\d)"),  # KR phone
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),  # email
)


def run_parse(raw_text: str, roles_form: list[dict]) -> dict:
    parsed = m1.parse(raw_text, roles_form)
    # Role contract: multiset(form) == multiset(parse). On mismatch the parse
    # loses and the form wins — roles are never an AI artifact.
    if m1.role_multiset(parsed["roles_requested"]) != m1.role_multiset(roles_form):
        parsed["roles_requested"] = [
            {
                "label": m1.normalize_role_label(str(role["label"]))[:40],
                "origin": "EXPLICIT",
                "evidence_span": str(role["label"]),
                "headcount": role.get("headcount"),
                "form_position": int(role["form_position"]),
            }
            for role in roles_form[:8]
        ]
    return parsed


def _apply_edits(parsed: dict, edits: dict) -> dict:
    """User corrections from the inferred-value sheet (S02a)."""
    result = dict(parsed)
    if "duration_weeks" in edits:
        weeks = edits["duration_weeks"]
        result["duration"] = {
            "weeks": weeks,
            "origin": "EXPLICIT" if weeks is not None else "NONE",
            "evidence_span": None,
        }
    if "compensation_is_paid" in edits or "compensation_amount_krw" in edits:
        compensation = dict(result["compensation"])
        if "compensation_is_paid" in edits:
            compensation["is_paid"] = bool(edits["compensation_is_paid"])
        if "compensation_amount_krw" in edits:
            compensation["amount_krw"] = edits["compensation_amount_krw"]
            compensation["currency"] = "KRW" if edits["compensation_amount_krw"] else "NONE"
        compensation["origin"] = "EXPLICIT"
        if not compensation["is_paid"]:
            compensation["amount_krw"] = None
            compensation["currency"] = "NONE"
        result["compensation"] = compensation
    if "signal_type" in edits and edits["signal_type"] in ("HELP", "WORK", "CIRCLE", "BOOKING"):
        result["signal_type"] = edits["signal_type"]
    return result


def _compensation_columns(parsed: dict) -> dict:
    compensation = parsed["compensation"]
    signal_type = parsed["signal_type"]
    is_paid = compensation["is_paid"]
    # Type invariants (CHECK constraints mirror these): CIRCLE unpaid, WORK/BOOKING paid.
    if signal_type == "CIRCLE":
        is_paid = False
    if signal_type in ("WORK", "BOOKING"):
        is_paid = True
    amount = compensation["amount_krw"] if is_paid else None
    return {
        "compensation_is_paid": is_paid,
        "compensation_amount_minor": amount,
        "compensation_currency": "KRW" if amount is not None else None,
        "compensation_origin": compensation["origin"]
        if compensation["origin"] != "NONE"
        else ("INFERRED" if signal_type in ("WORK", "BOOKING") and amount is None else "NONE"),
    }


async def create_draft(
    session: AsyncSession,
    *,
    requester: Profile,
    raw_text: str,
    roles_form: list[dict],
    edits: dict | None = None,
) -> Signal:
    if not 1 <= len(raw_text.strip()) <= 4000:
        raise ProductError(
            code="SIGNAL_TEXT_LENGTH", message="text must be 1–4000 characters", status_code=422
        )
    moderation_status = moderation.check(raw_text)
    parsed = _apply_edits(run_parse(raw_text, roles_form), edits or {})

    signal = Signal(
        requester_profile_id=requester.id,
        signal_type=parsed["signal_type"],
        raw_text=raw_text.strip(),
        status="DRAFT",
        moderation_status=moderation_status,
        matching_mode="RECRUITMENT" if parsed["signal_type"] == "CIRCLE" else "MATCH",
        visibility="PUBLIC",
        source_language=parsed["source_language"],
        urgency=parsed["urgency"],
        requires_physical_presence=parsed["location_requirement"]["requires_physical_presence"],
        area_hint=parsed["location_requirement"]["area_hint"],
        location_city_code=None,
        target_is_team=parsed["team_shape"]["target_is_team"],
        team_cardinality=parsed["team_shape"]["cardinality"],
        headcount_hint=parsed["team_shape"]["headcount_hint"],
        duration_weeks=parsed["duration"]["weeks"],
        duration_origin=parsed["duration"]["origin"] if parsed["duration"]["origin"] else "NONE",
        license_risk_flagged=parsed["license_risk"]["flagged"],
        license_risk_kind=parsed["license_risk"]["kind"],
        required_credentials=parsed["required_credentials"],
        policy_snapshot={
            "parse_schema_version": m1.SCHEMA_VERSION,
            "disclaimers": moderation.disclaimers_for(
                parsed["required_credentials"], parsed["signal_type"], parsed["urgency"]
            ),
        },
        **_compensation_columns(parsed),
    )
    session.add(signal)
    await session.flush()

    for role in parsed["roles_requested"]:
        session.add(
            SignalRole(
                signal_id=signal.id,
                label=role["label"],
                normalized_label=m1.normalize_role_label(role["label"]).lower(),
                headcount=role["headcount"],
                source="USER_FORM",
                form_position=role["form_position"],
                evidence_span=role["evidence_span"],
            )
        )
    for skill in parsed["skills"]:
        # importance is uncertainty metadata only — it is dropped right here (§1.5-G).
        session.add(
            SignalSkill(
                signal_id=signal.id,
                skill_name=skill["name"],
                origin=skill["origin"],
                evidence_span=skill["evidence_span"],
                confirmation_status="PENDING" if skill["origin"] == "INFERRED" else "NOT_REQUIRED",
            )
        )
    return signal


def _has_unconfirmed_inference(signal: Signal) -> bool:
    inferred_fields = (
        signal.duration_origin == "INFERRED" or signal.compensation_origin == "INFERRED"
    )
    return inferred_fields and signal.inference_confirmed_at is None


async def publish(
    session: AsyncSession, signal: Signal, *, requester: Profile, confirmations: dict
) -> Signal:
    """Publish gate — every condition must hold before DRAFT → OPEN (§6.4)."""
    if signal.status != "DRAFT":
        raise ProductError(
            code="SIGNAL_INVALID_TRANSITION",
            message="only drafts can be published",
            status_code=409,
        )
    if requester.status != "ACTIVE":
        raise ProductError(
            code="PROFILE_NOT_ACTIVE", message="profile is not active", status_code=422
        )
    roles = (
        await session.execute(select(SignalRole).where(SignalRole.signal_id == signal.id))
    ).scalars()
    if any(role.source != "USER_FORM" for role in roles):
        raise ProductError(
            code="SIGNAL_ROLE_SOURCE_INVALID",
            message="roles must come from the requester form",
            status_code=422,
        )

    now = datetime.now(UTC)
    if confirmations.get("inferred_confirmed"):
        signal.inference_confirmed_at = now
    if _has_unconfirmed_inference(signal):
        raise ProductError(
            code="SIGNAL_INFERENCE_CONFIRMATION_REQUIRED",
            message="estimated values need confirmation",
            status_code=422,
        )
    if signal.license_risk_flagged:
        if confirmations.get("license_acknowledged"):
            signal.license_risk_acknowledged_at = now
        if signal.license_risk_acknowledged_at is None:
            raise ProductError(
                code="SIGNAL_LICENSE_ACK_REQUIRED",
                message="derivative IP notice needs acknowledgement",
                status_code=422,
            )
    if {"MEDICAL_LICENSE", "LEGAL_LICENSE"} & set(signal.required_credentials):
        if confirmations.get("high_risk_acknowledged"):
            signal.high_risk_acknowledged_at = now
        if signal.high_risk_acknowledged_at is None:
            raise ProductError(
                code="SIGNAL_HIGH_RISK_DISCLAIMER_REQUIRED",
                message="high-risk disclaimer needs acknowledgement",
                status_code=422,
            )
    if signal.moderation_status != "ALLOWED":
        raise ProductError(
            code="SIGNAL_MODERATION_REVIEW_REQUIRED",
            message="the request is held for review",
            status_code=422,
        )
    if any(pattern.search(signal.raw_text) for pattern in PII_PATTERNS):
        raise ProductError(
            code="SIGNAL_PII_PRESENT",
            message="remove contact details from the request text",
            status_code=422,
        )

    signal.status = "OPEN"
    signal.published_at = now
    signal.version += 1
    return signal


async def get_owned(session: AsyncSession, signal_id: UUID, profile_id: UUID) -> Signal:
    signal = await session.get(Signal, signal_id)
    if signal is None:
        raise ProductError(code="SIGNAL_NOT_FOUND", message="signal not found", status_code=404)
    if signal.requester_profile_id != profile_id:
        raise ProductError(
            code="ACTING_PROFILE_FORBIDDEN", message="not the requester", status_code=403
        )
    return signal
