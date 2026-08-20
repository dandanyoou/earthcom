from datetime import time
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.model_base import Base, IdMixin, TimestampMixin


class Profile(IdMixin, TimestampMixin, Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("kind IN ('PERSON','TEAM')", name="kind_allowed"),
        CheckConstraint("char_length(display_name) BETWEEN 1 AND 80", name="name_length"),
        CheckConstraint("char_length(bio) <= 2000", name="bio_length"),
        CheckConstraint("status IN ('DRAFT','ACTIVE','HIDDEN','SUSPENDED')", name="status_allowed"),
        CheckConstraint("version > 0", name="version_positive"),
        CheckConstraint(
            "(kind = 'PERSON' AND owner_user_id IS NOT NULL) OR kind = 'TEAM'",
            name="person_has_owner",
        ),
        Index(
            "uq_person_profile_owner",
            "owner_user_id",
            unique=True,
            postgresql_where=text("kind = 'PERSON' AND status <> 'SUSPENDED'"),
        ),
    )

    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    owner_user_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    locale: Mapped[str] = mapped_column(String(2), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    city_code: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)


class Skill(IdMixin, TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint("char_length(display_name) BETWEEN 1 AND 80", name="name_length"),
    )

    normalized_name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)


class ProfileSkill(IdMixin, TimestampMixin, Base):
    __tablename__ = "profile_skills"
    __table_args__ = (
        UniqueConstraint("profile_id", "skill_id"),
        CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0", name="years_non_negative"
        ),
        CheckConstraint(
            "verification_status IN ('UNVERIFIED','PENDING','VERIFIED')",
            name="verification_allowed",
        ),
    )

    profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    skill_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("skills.id", ondelete="RESTRICT")
    )
    years_experience: Mapped[int | None] = mapped_column(SmallInteger)
    verification_status: Mapped[str] = mapped_column(String(16), nullable=False)


class ProfileLanguage(IdMixin, TimestampMixin, Base):
    __tablename__ = "profile_languages"
    __table_args__ = (
        UniqueConstraint("profile_id", "language_code"),
        CheckConstraint("language_code ~ '^[a-z]{2}$'", name="language_two_letters"),
        CheckConstraint(
            "proficiency IN ('BASIC','CONVERSATIONAL','PROFESSIONAL','NATIVE')",
            name="proficiency_allowed",
        ),
    )

    profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    language_code: Mapped[str] = mapped_column(String(2), nullable=False)
    proficiency: Mapped[str] = mapped_column(String(20), nullable=False)


class AvailabilityRule(IdMixin, TimestampMixin, Base):
    __tablename__ = "availability_rules"
    __table_args__ = (
        UniqueConstraint("profile_id", "rule_position"),
        CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_range"),
        CheckConstraint("local_start < local_end", name="time_order"),
        CheckConstraint("rule_position BETWEEN 0 AND 31", name="position_range"),
    )

    profile_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    local_start: Mapped[time] = mapped_column(Time, nullable=False)
    local_end: Mapped[time] = mapped_column(Time, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
