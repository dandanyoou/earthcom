"""Common AI response envelope (§7.2).

`ok=False` still carries a deterministic fallback in `data` — screens never go
blank because a model failed. Raw model output never leaves this envelope.
"""

from typing import Any

from app.platform.uuid7 import new_uuid7

DEGRADE_REASONS = (
    "SCHEMA_VIOLATION",
    "TIMEOUT",
    "TRUNCATED",
    "NO_EVIDENCE",
    "BUDGET",
    "MODERATION",
    "REFUSAL",
    "TRANSLATION_UNSAFE",
    "PROVIDER_UNAVAILABLE",
)


def envelope(
    *,
    module: str,
    data: Any,
    schema_version: str,
    mode: str,
    model: str = "deterministic",
    degraded: bool = False,
    degrade_reason: str | None = None,
    latency_ms: int = 0,
) -> dict[str, Any]:
    if degrade_reason is not None and degrade_reason not in DEGRADE_REASONS:
        raise ValueError(f"unknown degrade reason: {degrade_reason}")
    return {
        "ok": not degraded,
        "data": data,
        "degraded": degraded,
        "degrade_reason": degrade_reason,
        "meta": {
            "module": module,
            "model": model,
            "mode": mode,
            "latency_ms": latency_ms,
            "trace_id": str(new_uuid7()),
            "schema_version": schema_version,
        },
    }
