"""Message send orchestration and conversation serialization.

Order of operations (§6.6): membership → idempotency → moderation → guard
freshness → per-recipient translation with deterministic checks → lens with
the evidence gate. A failed translation ships the original with a review chip;
a self-harm signal never reaches any AI module.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat.models import (
    Conversation,
    GuardEvent,
    LensAnnotation,
    Message,
    MessageTranslation,
)
from app.domains.collaborations.models import Collaboration, CollaborationMember
from app.domains.kb.models import KbNorm
from app.domains.profiles.models import Profile
from app.errors import ProductError
from app.settings import Settings
from pangaea_ai import moderation
from pangaea_ai.modules import guard as m3
from pangaea_ai.modules import lens as m2
from pangaea_ai.modules import translate as m4


async def members_of(session: AsyncSession, conversation: Conversation) -> list[Profile]:
    rows = (
        await session.execute(
            select(Profile)
            .join(CollaborationMember, CollaborationMember.profile_id == Profile.id)
            .where(CollaborationMember.collaboration_id == conversation.collaboration_id)
        )
    ).scalars()
    return list(rows)


async def require_membership(
    session: AsyncSession, conversation_id: UUID, profile_id: UUID
) -> tuple[Conversation, list[Profile]]:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        raise ProductError(
            code="CONVERSATION_NOT_FOUND", message="conversation not found", status_code=404
        )
    members = await members_of(session, conversation)
    if profile_id not in {member.id for member in members}:
        raise ProductError(
            code="CONVERSATION_ACCESS_DENIED", message="not a member", status_code=403
        )
    return conversation, members


async def kb_ids(session: AsyncSession) -> set[str]:
    rows = await session.execute(select(KbNorm.id).where(KbNorm.status == "ACTIVE"))
    return set(rows.scalars())


async def kb_records(session: AsyncSession) -> dict[str, m2.KbRecord]:
    rows = (await session.execute(select(KbNorm).where(KbNorm.status == "ACTIVE"))).scalars()
    return {
        row.id: m2.KbRecord(
            id=row.id,
            claim=row.claim,
            scope_locale=row.scope_locale,
            scope_context=row.scope_context,
            confidence=float(row.confidence),
            verified_at=row.verified_at,
            dispute_count=len(row.disputes or []),
        )
        for row in rows
    }


def guard_payload(result: dict, text: str) -> dict:
    return {
        "display": result["display"],
        "rewritten_text": result.get("rewritten_text"),
        "risk": result["risk"],
        "phenomenon": result["phenomenon"],
        "reader_reading": result["reader_reading"],
        "suggestion": result["suggestion"],
        "kb_ids": result["kb_ids"],
        "guard_token": m3.input_hash(text),
    }


async def evaluate_guard(
    session: AsyncSession,
    *,
    conversation: Conversation,
    members: list[Profile],
    sender: Profile,
    text: str,
    settings: Settings,
) -> dict:
    target_langs = sorted({m.locale for m in members if m.id != sender.id and m.locale})
    result = m3.evaluate(
        text,
        source_lang=sender.locale,
        target_langs=target_langs,
        known_kb_ids=await kb_ids(session),
        min_confidence=settings.ai_guard_min_confidence,
    )
    return guard_payload(result, text)


async def send_message(
    session: AsyncSession,
    *,
    conversation: Conversation,
    members: list[Profile],
    sender: Profile,
    client_message_id: str,
    text: str,
    guard_token: str | None,
    guard_choice: str | None,
    settings: Settings,
) -> Message:
    existing = (
        await session.execute(
            select(Message).where(
                Message.conversation_id == conversation.id,
                Message.client_message_id == client_message_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing  # idempotent resend

    moderation_status = moderation.check(text)
    if moderation_status == "SELF_HARM_ROUTE":
        message = Message(
            conversation_id=conversation.id,
            sender_profile_id=sender.id,
            client_message_id=client_message_id,
            source_text=text,
            source_lang=sender.locale,
            delivery_status="NOT_SENT_SAFETY_ROUTE",
            moderation_status=moderation_status,
        )
        session.add(message)
        await session.flush()
        return message  # no AI pipeline for this branch

    guard_result = m3.evaluate(
        text,
        source_lang=sender.locale,
        target_langs=sorted({m.locale for m in members if m.id != sender.id and m.locale}),
        known_kb_ids=await kb_ids(session),
        min_confidence=settings.ai_guard_min_confidence,
    )
    if guard_result["display"] and guard_token != m3.input_hash(text):
        # The sender has not seen the warning for this exact text yet.
        raise ProductError(
            code="MESSAGE_GUARD_STALE",
            message="confirm the pre-send check first",
            status_code=409,
            details=guard_payload(guard_result, text),
        )

    message = Message(
        conversation_id=conversation.id,
        sender_profile_id=sender.id,
        client_message_id=client_message_id,
        source_text=text,
        source_lang=sender.locale,
        delivery_status="DELIVERED",
        moderation_status=moderation_status,
    )
    session.add(message)
    await session.flush()

    if guard_result["display"]:
        session.add(
            GuardEvent(
                conversation_id=conversation.id,
                sender_profile_id=sender.id,
                message_id=message.id,
                input_hash=m3.input_hash(text),
                risk=guard_result["risk"],
                phenomenon=guard_result["phenomenon"],
                choice=guard_choice if guard_choice in ("ORIGINAL", "SUGGESTION") else "ORIGINAL",
            )
        )
        # Deliberately no trust event here — warnings are not punished (§2.4-6).

    records = await kb_records(session)
    today = datetime.now(UTC).date()
    target_langs = sorted({m.locale for m in members if m.locale and m.locale != sender.locale})
    for target_lang in target_langs:
        translation = await m4.translate(
            text,
            source_lang=sender.locale,
            target_lang=target_lang,
            provider=settings.translate_provider,
            max_expansion=settings.ai_translate_max_expansion,
            api_key=settings.openai_api_key.get_secret_value(),
            base_url=settings.openai_base_url,
            model=settings.pangaea_model_low,
        )
        session.add(
            MessageTranslation(
                message_id=message.id,
                target_lang=target_lang,
                translated_text=translation.translated,
                status=translation.status,
            )
        )
        literal = translation.translated if translation.status == "READY" else text
        lens_result = m2.annotate(
            source_text=text,
            source_lang=sender.locale,
            literal=literal,
            kb_records=records,
            today=today,
            min_confidence=settings.ai_l3_min_confidence,
        )
        l3 = lens_result["l3"]
        session.add(
            LensAnnotation(
                message_id=message.id,
                target_lang=target_lang,
                l1_literal=lens_result["l1_literal"],
                l3_annotation=l3["annotation"] if l3 else None,
                l3_heading=l3["heading"] if l3 else None,
                l3_level=l3["level"] if l3 else None,
                l3_kb_ids=l3["kb_ids"] if l3 else [],
                publishable=bool(l3),
            )
        )
    return message


async def serialize_messages(
    session: AsyncSession,
    *,
    conversation: Conversation,
    members: list[Profile],
    viewer: Profile,
) -> list[dict]:
    member_by_id = {member.id: member for member in members}
    messages = (
        await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at, Message.id)
        )
    ).scalars()
    translations = {
        (row.message_id, row.target_lang): row
        for row in (
            await session.execute(
                select(MessageTranslation).where(
                    MessageTranslation.message_id.in_(
                        select(Message.id).where(Message.conversation_id == conversation.id)
                    )
                )
            )
        ).scalars()
    }
    lenses = {
        (row.message_id, row.target_lang): row
        for row in (
            await session.execute(
                select(LensAnnotation).where(
                    LensAnnotation.message_id.in_(
                        select(Message.id).where(Message.conversation_id == conversation.id)
                    )
                )
            )
        ).scalars()
    }
    guard_events = {
        row.message_id: row
        for row in (
            await session.execute(
                select(GuardEvent).where(GuardEvent.conversation_id == conversation.id)
            )
        ).scalars()
        if row.message_id is not None
    }

    payload: list[dict] = []
    for message in messages:
        sender = member_by_id.get(message.sender_profile_id)
        mine = message.sender_profile_id == viewer.id
        item: dict = {
            "id": str(message.id),
            "mine": mine,
            "sender": {
                "id": str(message.sender_profile_id),
                "name": sender.display_name if sender else "?",
                "locale": sender.locale if sender else "??",
            },
            "source_text": message.source_text,
            "source_lang": message.source_lang,
            "delivery_status": message.delivery_status,
            "created_at": message.created_at.isoformat(),
            "shown_text": message.source_text,
            "original_line": None,
            "translation_status": None,
            "help": None,
            "guard_badge": None,
            "receipts": [],
        }
        if mine:
            # What each other-language member actually received.
            receipts = []
            unsafe = False
            for member in members:
                if member.id == viewer.id or member.locale == message.source_lang:
                    continue
                translation = translations.get((message.id, member.locale))
                if translation is None:
                    continue
                if translation.status == "READY":
                    receipts.append(
                        {"name": member.display_name, "text": translation.translated_text}
                    )
                else:
                    unsafe = True
            item["receipts"] = receipts
            if unsafe:
                item["translation_status"] = "REVIEW_REQUIRED"
            event = guard_events.get(message.id)
            if event is not None:
                item["guard_badge"] = (
                    "CHECK_PASSED" if event.choice == "SUGGESTION" else "SENT_UNCHANGED"
                )
        else:
            translation = translations.get((message.id, viewer.locale))
            if translation is not None and translation.status == "READY":
                item["shown_text"] = translation.translated_text
                item["original_line"] = message.source_text
            elif translation is not None:
                item["translation_status"] = "REVIEW_REQUIRED"
            lens_row = lenses.get((message.id, viewer.locale))
            if lens_row is not None and lens_row.publishable:
                item["help"] = {
                    "heading": lens_row.l3_heading,
                    "level": lens_row.l3_level,
                    "annotation": lens_row.l3_annotation,
                    "kb_ids": lens_row.l3_kb_ids,
                }
        if message.delivery_status == "NOT_SENT_SAFETY_ROUTE":
            item["crisis_notice"] = moderation.CRISIS_NOTICE.get(
                viewer.locale, moderation.CRISIS_NOTICE["en"]
            )
        payload.append(item)
    return payload


async def conversation_summary(
    session: AsyncSession, conversation: Conversation, members: list[Profile]
) -> dict:
    collaboration = await session.get(Collaboration, conversation.collaboration_id)
    cities = [m.city_code for m in members if m.city_code]
    return {
        "id": str(conversation.id),
        "collaboration_id": str(conversation.collaboration_id),
        "title": collaboration.title if collaboration else "",
        "status": collaboration.status if collaboration else "",
        "member_count": len(members),
        "member_names": [m.display_name for m in members],
        "member_cities": cities,
        "translation_on": len({m.locale for m in members}) > 1,
    }
