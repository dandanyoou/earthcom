from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.model_base import Base, IdMixin, TimestampMixin


class Review(IdMixin, TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating IN ('POSITIVE','NEUTRAL','NEGATIVE')", name="rating_allowed"),
        CheckConstraint("char_length(comment) <= 500", name="comment_length"),
        CheckConstraint("reviewer_profile_id <> reviewee_profile_id", name="no_self_review"),
        UniqueConstraint("collaboration_id", "reviewer_profile_id", "reviewee_profile_id"),
    )

    collaboration_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("collaborations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reviewer_profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    reviewee_profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    rating: Mapped[str] = mapped_column(String(16), nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(24)), nullable=False, default=list)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")


class TrustEvent(IdMixin, Base):
    """Append-only input of trust.v1. Guard events must never create rows here.

    DEMO_SEED rows exist only for seeded demo accounts (is_demo). Their delta is stored
    on the row so the projection stays deterministic; every other key maps through the
    fixed DELTA table in app/policies/trust.py.
    """

    __tablename__ = "trust_events"
    __table_args__ = (
        CheckConstraint(
            "event_key IN ('COLLABORATION_COMPLETED','NO_SHOW_CONFIRMED',"
            "'REVIEW_RECEIVED:POSITIVE','REVIEW_RECEIVED:NEUTRAL','REVIEW_RECEIVED:NEGATIVE',"
            "'DISPUTE_RESOLVED:AT_FAULT','DISPUTE_RESOLVED:OTHER','DEMO_SEED')",
            name="event_key_allowed",
        ),
        CheckConstraint(
            "(event_key = 'DEMO_SEED') = (demo_delta IS NOT NULL)",
            name="demo_delta_only_for_seed",
        ),
        Index("ix_trust_events_profile_created", "profile_id", "created_at"),
    )

    profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    event_key: Mapped[str] = mapped_column(String(32), nullable=False)
    demo_delta: Mapped[float | None] = mapped_column(Numeric(4, 2))
    source_collaboration_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("collaborations.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
