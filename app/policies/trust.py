"""trust.v1 — deterministic trust temperature. LLMs never touch this file.

The projection reads the append-only trust_events log and nothing else.
Guard events (ignored pre-send warnings) are not an input by design (§2.4-6).
DEMO_SEED events exist only for seeded demo profiles and carry their delta on
the row, so replaying the log always yields the same value.
"""

from dataclasses import dataclass

BASE = 36.5
DELTA = {
    "COLLABORATION_COMPLETED": +1.2,
    "NO_SHOW_CONFIRMED": -2.0,
    "REVIEW_RECEIVED:POSITIVE": +0.3,
    "REVIEW_RECEIVED:NEUTRAL": 0.0,
    "REVIEW_RECEIVED:NEGATIVE": -0.8,
    "DISPUTE_RESOLVED:AT_FAULT": -1.0,
    "DISPUTE_RESOLVED:OTHER": 0.0,
}
FLOOR, CEIL = 30.0, 50.0


@dataclass(frozen=True)
class TrustEventInput:
    event_key: str
    demo_delta: float | None = None


@dataclass(frozen=True)
class TrustProjection:
    status: str  # AVAILABLE | UNAVAILABLE
    value: float | None
    is_demo: bool
    policy_version: str


def event_delta(event: TrustEventInput) -> float:
    if event.event_key == "DEMO_SEED":
        if event.demo_delta is None:
            raise ValueError("DEMO_SEED events must carry demo_delta")
        return float(event.demo_delta)
    return DELTA[event.event_key]


def project(events: list[TrustEventInput], *, policy_version: str = "trust.v1") -> TrustProjection:
    if policy_version == "disabled":
        return TrustProjection(
            status="UNAVAILABLE", value=None, is_demo=False, policy_version=policy_version
        )
    value = BASE + sum(event_delta(event) for event in events)
    clamped = round(min(CEIL, max(FLOOR, value)), 1)
    is_demo = any(event.event_key == "DEMO_SEED" for event in events)
    return TrustProjection(
        status="AVAILABLE", value=clamped, is_demo=is_demo, policy_version=policy_version
    )
