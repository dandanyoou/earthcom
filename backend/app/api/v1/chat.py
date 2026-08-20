"""Conversations (S04): summary, message history, orchestrated send."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat import service as chat
from app.domains.chat.models import Conversation
from app.domains.collaborations.models import Collaboration, CollaborationMember
from app.envelope import ok
from app.platform.authz import Identity, get_identity, require_profile
from app.platform.db import get_db_session
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1/conversations", tags=["chat"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
IdentityDep = Annotated[Identity, Depends(get_identity)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


class MessageInput(BaseModel):
    client_message_id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=2000)
    guard_token: str | None = None
    guard_choice: str | None = Field(default=None, pattern="^(ORIGINAL|SUGGESTION)$")


@router.get("")
async def list_conversations(session: SessionDep, identity: IdentityDep):
    profile = require_profile(identity)
    rows = list(
        (
            await session.execute(
                select(Conversation)
                .join(Collaboration, Collaboration.id == Conversation.collaboration_id)
                .join(
                    CollaborationMember,
                    CollaborationMember.collaboration_id == Collaboration.id,
                )
                .where(CollaborationMember.profile_id == profile.id)
                .order_by(Conversation.created_at.desc())
            )
        ).scalars()
    )
    payload = []
    for conversation in rows:
        members = await chat.members_of(session, conversation)
        payload.append(await chat.conversation_summary(session, conversation, members))
    return ok(payload)


@router.get("/{conversation_id}")
async def conversation_detail(conversation_id: UUID, session: SessionDep, identity: IdentityDep):
    profile = require_profile(identity)
    conversation, members = await chat.require_membership(session, conversation_id, profile.id)
    return ok(await chat.conversation_summary(session, conversation, members))


@router.get("/{conversation_id}/messages")
async def list_messages(conversation_id: UUID, session: SessionDep, identity: IdentityDep):
    profile = require_profile(identity)
    conversation, members = await chat.require_membership(session, conversation_id, profile.id)
    return ok(
        await chat.serialize_messages(
            session, conversation=conversation, members=members, viewer=profile
        )
    )


@router.post("/{conversation_id}/messages", status_code=201)
async def send_message(
    conversation_id: UUID,
    body: MessageInput,
    session: SessionDep,
    identity: IdentityDep,
    settings: SettingsDep,
):
    profile = require_profile(identity)
    conversation, members = await chat.require_membership(session, conversation_id, profile.id)
    message = await chat.send_message(
        session,
        conversation=conversation,
        members=members,
        sender=profile,
        client_message_id=body.client_message_id,
        text=body.text,
        guard_token=body.guard_token,
        guard_choice=body.guard_choice,
        settings=settings,
    )
    await session.commit()
    serialized = await chat.serialize_messages(
        session, conversation=conversation, members=members, viewer=profile
    )
    sent = next((item for item in serialized if item["id"] == str(message.id)), None)
    return ok(sent or {"id": str(message.id)})
