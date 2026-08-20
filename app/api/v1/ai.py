"""AI expression endpoints. These return the E3 envelope directly (§6.1),
never re-wrapped: parse preview (S02), pre-send guard (S04), search widening.
"""

import time as time_module
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat import service as chat
from app.domains.signals.service import run_parse
from app.platform.authz import Identity, get_identity
from app.platform.db import get_db_session
from app.settings import Settings, get_settings
from pangaea_ai import moderation
from pangaea_ai.envelope import envelope
from pangaea_ai.modules import parse as m1
from pangaea_ai.modules import search as m8

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
IdentityDep = Annotated[Identity, Depends(get_identity)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


class RoleForm(BaseModel):
    label: str = Field(min_length=1, max_length=40)
    headcount: int | None = Field(default=None, ge=1, le=50)
    form_position: int = Field(ge=0, le=7)


class ParseInput(BaseModel):
    raw_text: str = Field(min_length=1, max_length=4000)
    roles_form: list[RoleForm] = Field(default_factory=list, max_length=8)


class GuardInput(BaseModel):
    conversation_id: UUID
    text: str = Field(min_length=1, max_length=2000)


class SearchNormalizeInput(BaseModel):
    query: str = Field(min_length=1, max_length=120)


@router.post("/parse")
async def ai_parse(body: ParseInput, identity: IdentityDep, settings: SettingsDep):
    started = time_module.monotonic()
    if moderation.check(body.raw_text) == "SELF_HARM_ROUTE":
        # The parser is never called on this branch (§9.5).
        return envelope(
            module="parse",
            data={
                "crisis_notice": moderation.CRISIS_NOTICE.get(
                    identity.locale, moderation.CRISIS_NOTICE["en"]
                )
            },
            schema_version=m1.SCHEMA_VERSION,
            mode=settings.ai_mode,
            degraded=True,
            degrade_reason="MODERATION",
        )
    parsed = run_parse(body.raw_text, [role.model_dump() for role in body.roles_form])
    disclaimers = moderation.disclaimers_for(
        parsed["required_credentials"], parsed["signal_type"], parsed["urgency"]
    )
    return envelope(
        module="parse",
        data={**parsed, "disclaimers": disclaimers},
        schema_version=m1.SCHEMA_VERSION,
        mode=settings.ai_mode,
        latency_ms=int((time_module.monotonic() - started) * 1000),
    )


@router.post("/guard")
async def ai_guard(
    body: GuardInput, session: SessionDep, identity: IdentityDep, settings: SettingsDep
):
    started = time_module.monotonic()
    conversation, members = await chat.require_membership(
        session, body.conversation_id, identity.profile_id
    )
    sender = next(member for member in members if member.id == identity.profile_id)
    payload = await chat.evaluate_guard(
        session,
        conversation=conversation,
        members=members,
        sender=sender,
        text=body.text,
        settings=settings,
    )
    return envelope(
        module="guard",
        data=payload,
        schema_version="guard.v2",
        mode=settings.ai_mode,
        latency_ms=int((time_module.monotonic() - started) * 1000),
    )


@router.post("/search-normalize")
async def ai_search_normalize(body: SearchNormalizeInput, settings: SettingsDep):
    return envelope(
        module="search",
        data=m8.normalize(body.query),
        schema_version=m8.SCHEMA_VERSION,
        mode=settings.ai_mode,
    )
