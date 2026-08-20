from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.model_base import Base, IdMixin, TimestampMixin

DEPOSIT_STATUSES = (
    "PROPOSED",
    "AGREED",
    "FUNDING",
    "LOCKED",
    "REFUND_PENDING",
    "REFUNDED",
    "DISPUTED",
    "CANCELLED",
)


class DepositAgreement(IdMixin, TimestampMixin, Base):
    """Promise deposits only. Work payment, split, or settlement fields must not exist."""

    __tablename__ = "deposit_agreements"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PROPOSED','AGREED','FUNDING','LOCKED','REFUND_PENDING','REFUNDED',"
            "'DISPUTED','CANCELLED')",
            name="status_allowed",
        ),
        CheckConstraint("amount_minor_per_party > 0", name="amount_positive"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_iso"),
    )

    collaboration_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("collaborations.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PROPOSED")
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount_minor_per_party: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cap_policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    terms_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class DepositParty(IdMixin, TimestampMixin, Base):
    __tablename__ = "deposit_parties"
    __table_args__ = (UniqueConstraint("agreement_id", "profile_id"),)

    agreement_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("deposit_agreements.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    agreed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    funded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DepositLedgerEntry(IdMixin, Base):
    """Append-only ledger; provider events are idempotent via provider_event_id."""

    __tablename__ = "deposit_ledger_entries"
    __table_args__ = (
        CheckConstraint("entry_type IN ('FUND','REFUND')", name="entry_type_allowed"),
        CheckConstraint("amount_minor > 0", name="amount_positive"),
        UniqueConstraint("provider_event_id"),
    )

    agreement_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("deposit_agreements.id", ondelete="RESTRICT"),
        nullable=False,
    )
    profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    entry_type: Mapped[str] = mapped_column(String(8), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
