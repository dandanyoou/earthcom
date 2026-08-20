from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.model_base import Base, IdMixin, TimestampMixin


class Conversation(IdMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    collaboration_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("collaborations.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )


class Message(IdMixin, TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("conversation_id", "client_message_id"),
        CheckConstraint("source_lang ~ '^[a-z]{2}$'", name="source_lang_two_letters"),
        CheckConstraint(
            "delivery_status IN ('ACCEPTED','DELIVERED','HELD_FOR_REVIEW',"
            "'NOT_SENT_SAFETY_ROUTE','FAILED')",
            name="delivery_allowed",
        ),
        CheckConstraint(
            "moderation_status IN ('ALLOWED','PENDING_REVIEW','BLOCKED','SELF_HARM_ROUTE')",
            name="moderation_allowed",
        ),
        CheckConstraint("char_length(source_text) BETWEEN 1 AND 2000", name="source_text_length"),
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sender_profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    client_message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_lang: Mapped[str] = mapped_column(String(2), nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(24), nullable=False, default="DELIVERED")
    moderation_status: Mapped[str] = mapped_column(String(24), nullable=False, default="ALLOWED")


class MessageTranslation(IdMixin, TimestampMixin, Base):
    __tablename__ = "message_translations"
    __table_args__ = (
        UniqueConstraint("message_id", "target_lang"),
        CheckConstraint("target_lang ~ '^[a-z]{2}$'", name="target_lang_two_letters"),
        CheckConstraint("status IN ('READY','UNSAFE_OR_FAILED','PENDING')", name="status_allowed"),
    )

    message_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    target_lang: Mapped[str] = mapped_column(String(2), nullable=False)
    translated_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), nullable=False)


class LensAnnotation(IdMixin, TimestampMixin, Base):
    """L1 literal is always present; L3 renders only when the evidence gate passed."""

    __tablename__ = "lens_annotations"
    __table_args__ = (
        UniqueConstraint("message_id", "target_lang"),
        CheckConstraint(
            "l3_level IN ('STRONG','MODERATE','REFERENCE') OR l3_level IS NULL",
            name="l3_level_allowed",
        ),
    )

    message_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    target_lang: Mapped[str] = mapped_column(String(2), nullable=False)
    l1_literal: Mapped[str] = mapped_column(Text, nullable=False)
    l3_annotation: Mapped[str | None] = mapped_column(Text)
    l3_heading: Mapped[str | None] = mapped_column(String(16))
    l3_level: Mapped[str | None] = mapped_column(String(16))
    l3_kb_ids: Mapped[list[str]] = mapped_column(ARRAY(String(8)), nullable=False, default=list)
    publishable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class GuardEvent(IdMixin, Base):
    """Audit trail only. Guard events never feed trust_events (§2.4-6)."""

    __tablename__ = "guard_events"
    __table_args__ = (
        CheckConstraint("choice IN ('ORIGINAL','SUGGESTION')", name="choice_allowed"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sender_profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    message_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL")
    )
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    risk: Mapped[str] = mapped_column(String(8), nullable=False)
    phenomenon: Mapped[str] = mapped_column(String(32), nullable=False)
    choice: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
