from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.model_base import Base, IdMixin, TimestampMixin

SIGNAL_STATUSES = (
    "DRAFT",
    "OPEN",
    "PAUSED",
    "IN_PROGRESS",
    "CLOSED",
    "EXPIRED",
    "CANCELLED",
    "COMPLETED",
)


class Signal(IdMixin, TimestampMixin, Base):
    __tablename__ = "signals"
    __table_args__ = (
        CheckConstraint(
            "signal_type IN ('HELP','WORK','CIRCLE','BOOKING')", name="signal_type_allowed"
        ),
        CheckConstraint(
            "status IN ('DRAFT','OPEN','PAUSED','IN_PROGRESS','CLOSED','EXPIRED',"
            "'CANCELLED','COMPLETED')",
            name="status_allowed",
        ),
        CheckConstraint(
            "moderation_status IN ('ALLOWED','PENDING_REVIEW','BLOCKED','SELF_HARM_ROUTE')",
            name="moderation_allowed",
        ),
        CheckConstraint("matching_mode IN ('MATCH','RECRUITMENT')", name="matching_mode_allowed"),
        CheckConstraint(
            "visibility IN ('PUBLIC','LINK_ONLY','PRIVATE')", name="visibility_allowed"
        ),
        CheckConstraint("source_language ~ '^[a-z]{2}$'", name="source_language_two_letters"),
        CheckConstraint("urgency IN ('CRITICAL','HIGH','NORMAL','LOW')", name="urgency_allowed"),
        CheckConstraint("team_cardinality IN ('1:1','1:N','N:N')", name="cardinality_allowed"),
        CheckConstraint(
            "headcount_hint IS NULL OR headcount_hint BETWEEN 1 AND 50", name="headcount_range"
        ),
        CheckConstraint(
            "duration_weeks IS NULL OR duration_weeks BETWEEN 1 AND 104", name="duration_range"
        ),
        CheckConstraint(
            "duration_origin IN ('EXPLICIT','INFERRED','DEFAULT','NONE')",
            name="duration_origin_allowed",
        ),
        CheckConstraint(
            "compensation_origin IN ('EXPLICIT','INFERRED','NONE')",
            name="compensation_origin_allowed",
        ),
        CheckConstraint(
            "(compensation_amount_minor IS NULL AND compensation_currency IS NULL)"
            " OR (compensation_amount_minor IS NOT NULL AND compensation_currency IS NOT NULL)",
            name="compensation_pairing",
        ),
        CheckConstraint(
            "compensation_is_paid = true OR compensation_amount_minor IS NULL",
            name="unpaid_has_no_amount",
        ),
        CheckConstraint(
            "(signal_type = 'CIRCLE' AND compensation_is_paid = false)"
            " OR (signal_type IN ('WORK','BOOKING') AND compensation_is_paid = true)"
            " OR signal_type = 'HELP'",
            name="type_compensation_rule",
        ),
        CheckConstraint(
            "license_risk_kind IN ('DERIVATIVE_IP','TRADEMARK','NONE')",
            name="license_kind_allowed",
        ),
        CheckConstraint("char_length(raw_text) BETWEEN 1 AND 4000", name="raw_text_length"),
        Index("ix_signals_status_published_at", "status", "published_at"),
    )

    requester_profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    signal_type: Mapped[str] = mapped_column(String(16), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    moderation_status: Mapped[str] = mapped_column(String(24), nullable=False, default="ALLOWED")
    matching_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="MATCH")
    visibility: Mapped[str] = mapped_column(String(16), nullable=False, default="PUBLIC")
    source_language: Mapped[str] = mapped_column(String(2), nullable=False)
    urgency: Mapped[str] = mapped_column(String(16), nullable=False, default="NORMAL")
    requires_physical_presence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    area_hint: Mapped[str | None] = mapped_column(String(60))
    location_city_code: Mapped[str | None] = mapped_column(String(32))
    target_is_team: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    team_cardinality: Mapped[str] = mapped_column(String(4), nullable=False, default="1:N")
    headcount_hint: Mapped[int | None] = mapped_column(SmallInteger)
    duration_weeks: Mapped[int | None] = mapped_column(SmallInteger)
    duration_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="NONE")
    compensation_is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    compensation_amount_minor: Mapped[int | None] = mapped_column(Integer)
    compensation_currency: Mapped[str | None] = mapped_column(String(3))
    compensation_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="NONE")
    license_risk_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    license_risk_kind: Mapped[str] = mapped_column(String(16), nullable=False, default="NONE")
    license_risk_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    required_credentials: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)), nullable=False, default=list
    )
    high_risk_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inference_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    policy_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class SignalRole(IdMixin, TimestampMixin, Base):
    """Roles come from the requester's form only. AI-designed roles are unrepresentable."""

    __tablename__ = "signal_roles"
    __table_args__ = (
        CheckConstraint("char_length(label) BETWEEN 1 AND 40", name="label_length"),
        CheckConstraint("source = 'USER_FORM'", name="source_user_form_only"),
        CheckConstraint("headcount IS NULL OR headcount BETWEEN 1 AND 50", name="headcount_range"),
        CheckConstraint("filled_count >= 0", name="filled_non_negative"),
        CheckConstraint("form_position BETWEEN 0 AND 7", name="form_position_range"),
        UniqueConstraint("signal_id", "form_position"),
    )

    signal_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("signals.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(40), nullable=False)
    normalized_label: Mapped[str] = mapped_column(String(40), nullable=False)
    headcount: Mapped[int | None] = mapped_column(SmallInteger)
    filled_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="USER_FORM")
    form_position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    evidence_span: Mapped[str | None] = mapped_column(Text)


class SignalSkill(IdMixin, TimestampMixin, Base):
    __tablename__ = "signal_skills"
    __table_args__ = (
        CheckConstraint("char_length(skill_name) BETWEEN 1 AND 40", name="skill_name_length"),
        CheckConstraint("origin IN ('EXPLICIT','INFERRED','USER_EDITED')", name="origin_allowed"),
        CheckConstraint(
            "confirmation_status IN ('NOT_REQUIRED','PENDING','CONFIRMED','REJECTED')",
            name="confirmation_allowed",
        ),
    )

    signal_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("signals.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String(40), nullable=False)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    evidence_span: Mapped[str | None] = mapped_column(Text)
    confirmation_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="NOT_REQUIRED"
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
