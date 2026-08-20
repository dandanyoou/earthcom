from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, Date, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.model_base import Base, IdMixin, TimestampMixin

EMBED_DIMENSIONS = 1536  # Contract. Changing it requires a migration and agreement.


class KbNorm(Base):
    """Cultural knowledge base. scope_locale is a language sphere, never a nationality."""

    __tablename__ = "kb_norms"
    __table_args__ = (
        CheckConstraint("id ~ '^[A-Z]{2}-[0-9]{3}$'", name="id_pattern"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("status IN ('ACTIVE','RETIRED','CANDIDATE')", name="status_allowed"),
        CheckConstraint(
            "status <> 'ACTIVE' OR jsonb_array_length(sources) >= 2", name="sources_min"
        ),
    )

    id: Mapped[str] = mapped_column(String(6), primary_key=True)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    scope_locale: Mapped[str] = mapped_column(String(2), nullable=False)
    scope_context: Mapped[str] = mapped_column(String(32), nullable=False)
    sources: Mapped[list] = mapped_column(JSONB, nullable=False)
    verified_at: Mapped[date] = mapped_column(Date, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    disputes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBED_DIMENSIONS), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )


class KbCandidate(IdMixin, TimestampMixin, Base):
    """Detected neologisms awaiting curation. Gloss is an AI guess, never a fact."""

    __tablename__ = "kb_candidates"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','APPROVED','REJECTED')", name="status_allowed"),
        CheckConstraint("detected_confidence BETWEEN 0 AND 1", name="confidence_range"),
    )

    term: Mapped[str] = mapped_column(String(60), nullable=False)
    gloss: Mapped[str | None] = mapped_column(Text)
    detected_confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
