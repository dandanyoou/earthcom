from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.model_base import Base, IdMixin, TimestampMixin

COLLABORATION_STATUSES = (
    "AGREEMENT_PENDING",
    "DEPOSIT_PENDING",
    "ACTIVE",
    "COMPLETION_PENDING",
    "COMPLETED",
    "DISPUTED",
    "CANCELLED",
)


class Application(IdMixin, TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (
        CheckConstraint("direction IN ('APPLICATION','INVITATION')", name="direction_allowed"),
        CheckConstraint(
            "status IN ('PENDING','ACCEPTED','REJECTED','WITHDRAWN')", name="status_allowed"
        ),
        CheckConstraint("char_length(message) <= 1000", name="message_length"),
        UniqueConstraint("signal_id", "applicant_profile_id", "direction"),
    )

    signal_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("signals.id", ondelete="CASCADE"), nullable=False
    )
    applicant_profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    role_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("signal_roles.id", ondelete="SET NULL")
    )
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Collaboration(IdMixin, TimestampMixin, Base):
    __tablename__ = "collaborations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('AGREEMENT_PENDING','DEPOSIT_PENDING','ACTIVE','COMPLETION_PENDING',"
            "'COMPLETED','DISPUTED','CANCELLED')",
            name="status_allowed",
        ),
        CheckConstraint("char_length(title) BETWEEN 1 AND 120", name="title_length"),
    )

    signal_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("signals.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="AGREEMENT_PENDING")
    deposit_applies: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class CollaborationMember(IdMixin, TimestampMixin, Base):
    __tablename__ = "collaboration_members"
    __table_args__ = (
        UniqueConstraint("collaboration_id", "profile_id"),
        CheckConstraint("char_length(role_label) BETWEEN 1 AND 40", name="role_label_length"),
    )

    collaboration_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("collaborations.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    role_label: Mapped[str] = mapped_column(String(40), nullable=False)
    is_requester: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CompletionConfirmation(IdMixin, TimestampMixin, Base):
    """One row per member; the collaboration completes when every member confirmed."""

    __tablename__ = "completion_confirmations"
    __table_args__ = (UniqueConstraint("collaboration_id", "profile_id"),)

    collaboration_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("collaborations.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CollaborationDeliverable(IdMixin, TimestampMixin, Base):
    __tablename__ = "collaboration_deliverables"
    __table_args__ = (
        UniqueConstraint("collaboration_id", "position"),
        CheckConstraint("char_length(file_name) BETWEEN 1 AND 120", name="file_name_length"),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="hash_sha256"),
    )

    collaboration_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("collaborations.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(String(120), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
