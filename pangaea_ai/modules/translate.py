"""M4 outbound translation with deterministic safety checks.

Two providers:
- stub    — fixture dictionary (network 0). Unknown text fails safe: the
            message ships as the original with a "translation review" chip.
- openai  — OpenAI Responses API. The key lives in the server process only.

Whatever the provider says, the numeral-multiset and expansion checks are
machine-verified here. A failed check never blocks sending and never ships a
silently wrong translation: the original goes out, flagged (§2.4-3).
"""

import json
from dataclasses import dataclass
from typing import Any

import httpx

from pangaea_ai import lexicon
from pangaea_ai.gates import expansion_ok, numeral_multiset_ok
from pangaea_ai.modules.guard import input_hash as _hash  # noqa: F401  (kept for cache keys)

SCHEMA_VERSION = "translate.v1"

_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["translated", "intent_preserved", "additions_made"],
    "properties": {
        "translated": {"type": "string", "maxLength": 1200},
        "intent_preserved": {"type": "boolean"},
        "additions_made": {"type": "boolean"},
    },
}

_SYSTEM_PROMPT = (
    "You translate one chat message between collaborators. Preserve intent, "
    "register, and every numeral exactly. Never add promises, dates, numbers, "
    "or apologies that are not in the source. If you cannot translate "
    "faithfully, set intent_preserved to false."
)


@dataclass(frozen=True)
class TranslationResult:
    status: str  # READY | UNSAFE_OR_FAILED
    translated: str | None
    provider: str
    failure_reason: str | None = None


def _fixture_lookup(text: str, target_lang: str) -> str | None:
    per_target = lexicon.TRANSLATION_FIXTURES.get(text.strip())
    if per_target:
        return per_target.get(target_lang)
    return None


def _safety_check(source: str, translated: str, max_expansion: float) -> str | None:
    if not numeral_multiset_ok(source, translated):
        return "NUMERAL_MISMATCH"
    if not expansion_ok(source, translated, max_expansion):
        return "LENGTH_BLOWUP"
    return None


async def _openai_translate(
    text: str,
    *,
    source_lang: str,
    target_lang: str,
    api_key: str,
    base_url: str,
    model: str,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "instructions": _SYSTEM_PROMPT,
        "input": [
            {
                "role": "user",
                "content": (
                    f"[source language] {source_lang}\n[target language] {target_lang}\n"
                    f"[message]\n{text}"
                ),
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "translation",
                "schema": _RESPONSE_SCHEMA,
                "strict": True,
            }
        },
        "max_output_tokens": 600,
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.post(
            f"{base_url}/responses",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
    for item in body.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "refusal":
                raise RuntimeError("refusal")
            if content.get("type") == "output_text":
                return json.loads(content["text"])
    raise RuntimeError("no output text")


async def translate(
    text: str,
    *,
    source_lang: str,
    target_lang: str,
    provider: str,
    max_expansion: float = 2.5,
    api_key: str = "",
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
) -> TranslationResult:
    if source_lang == target_lang:
        return TranslationResult(status="READY", translated=text, provider="identity")

    if provider == "openai" and api_key:
        try:
            parsed = await _openai_translate(
                text,
                source_lang=source_lang,
                target_lang=target_lang,
                api_key=api_key,
                base_url=base_url,
                model=model,
            )
        except Exception:
            return TranslationResult(
                status="UNSAFE_OR_FAILED",
                translated=None,
                provider="openai",
                failure_reason="PROVIDER_ERROR",
            )
        if parsed.get("additions_made") or not parsed.get("intent_preserved", False):
            return TranslationResult(
                status="UNSAFE_OR_FAILED",
                translated=None,
                provider="openai",
                failure_reason="SELF_REPORTED_UNSAFE",
            )
        translated = str(parsed.get("translated", ""))
        failure = _safety_check(text, translated, max_expansion)
        if failure:
            return TranslationResult(
                status="UNSAFE_OR_FAILED",
                translated=None,
                provider="openai",
                failure_reason=failure,
            )
        return TranslationResult(status="READY", translated=translated, provider="openai")

    fixture = _fixture_lookup(text, target_lang)
    if fixture is not None:
        failure = _safety_check(text, fixture, max_expansion)
        if failure is None:
            return TranslationResult(status="READY", translated=fixture, provider="stub")
    return TranslationResult(
        status="UNSAFE_OR_FAILED",
        translated=None,
        provider="stub",
        failure_reason="NO_FIXTURE",
    )
