from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.model_base import Base, IdMixin, TimestampMixin

NOTIFICATION_KINDS = (
    "APPLICATION_RECEIVED",
    "APPLICATION_ACCEPTED",
    "APPLICATION_REJECTED",
    "DEPOSIT_UPDATED",
    "MESSAGE_RECEIVED",
    "COMPLETION_REQUESTED",
    "COLLABORATION_COMPLETED",
    "REVIEW_RECEIVED",
)


class Notification(IdMixin, TimestampMixin, Base):
    """Kind + payload only; the client renders localized copy from its catalog."""

    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('APPLICATION_RECEIVED','APPLICATION_ACCEPTED','APPLICATION_REJECTED',"
            "'DEPOSIT_UPDATED','MESSAGE_RECEIVED','COMPLETION_REQUESTED',"
            "'COLLABORATION_COMPLETED','REVIEW_RECEIVED')",
            name="kind_allowed",
        ),
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    resource_type: Mapped[str | None] = mapped_column(String(32))
    resource_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
