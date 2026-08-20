"""Create identity and profile foundations.

Revision ID: 0001
Revises:
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("default_locale", sa.String(length=2), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('ACTIVE','SUSPENDED','DELETION_PENDING','DELETED')",
            name="ck_users_status_allowed",
        ),
        sa.CheckConstraint("default_locale ~ '^[a-z]{2}$'", name="ck_users_locale_two_letters"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("bio", sa.Text(), server_default="", nullable=False),
        sa.Column("locale", sa.String(length=2), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("city_code", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint("kind IN ('PERSON','TEAM')", name="ck_profiles_kind_allowed"),
        sa.CheckConstraint(
            "char_length(display_name) BETWEEN 1 AND 80", name="ck_profiles_name_length"
        ),
        sa.CheckConstraint("char_length(bio) <= 2000", name="ck_profiles_bio_length"),
        sa.CheckConstraint(
            "status IN ('DRAFT','ACTIVE','HIDDEN','SUSPENDED')",
            name="ck_profiles_status_allowed",
        ),
        sa.CheckConstraint("version > 0", name="ck_profiles_version_positive"),
        sa.CheckConstraint(
            "(kind = 'PERSON' AND owner_user_id IS NOT NULL) OR kind = 'TEAM'",
            name="ck_profiles_person_has_owner",
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name="fk_profiles_owner_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_profiles"),
    )
    op.create_index(
        "uq_person_profile_owner",
        "profiles",
        ["owner_user_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'PERSON' AND status <> 'SUSPENDED'"),
    )
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("normalized_name", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "char_length(display_name) BETWEEN 1 AND 80", name="ck_skills_name_length"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_skills"),
        sa.UniqueConstraint("normalized_name", name="uq_skills_normalized_name"),
    )
    op.create_table(
        "profile_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("years_experience", sa.SmallInteger(), nullable=True),
        sa.Column("verification_status", sa.String(length=16), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0",
            name="ck_profile_skills_years_non_negative",
        ),
        sa.CheckConstraint(
            "verification_status IN ('UNVERIFIED','PENDING','VERIFIED')",
            name="ck_profile_skills_verification_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["profiles.id"],
            name="fk_profile_skills_profile_id_profiles",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name="fk_profile_skills_skill_id_skills",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_profile_skills"),
        sa.UniqueConstraint("profile_id", "skill_id", name="uq_profile_skills_profile_id"),
    )
    op.create_table(
        "profile_languages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language_code", sa.String(length=2), nullable=False),
        sa.Column("proficiency", sa.String(length=20), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "language_code ~ '^[a-z]{2}$'", name="ck_profile_languages_language_two_letters"
        ),
        sa.CheckConstraint(
            "proficiency IN ('BASIC','CONVERSATIONAL','PROFESSIONAL','NATIVE')",
            name="ck_profile_languages_proficiency_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["profiles.id"],
            name="fk_profile_languages_profile_id_profiles",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_profile_languages"),
        sa.UniqueConstraint("profile_id", "language_code", name="uq_profile_languages_profile_id"),
    )
    op.create_table(
        "availability_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("local_start", sa.Time(), nullable=False),
        sa.Column("local_end", sa.Time(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("rule_position", sa.SmallInteger(), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_availability_rules_weekday_range"),
        sa.CheckConstraint("local_start < local_end", name="ck_availability_rules_time_order"),
        sa.CheckConstraint(
            "rule_position BETWEEN 0 AND 31", name="ck_availability_rules_position_range"
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["profiles.id"],
            name="fk_availability_rules_profile_id_profiles",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_availability_rules"),
        sa.UniqueConstraint("profile_id", "rule_position", name="uq_availability_rules_profile_id"),
    )


def downgrade() -> None:
    op.drop_table("availability_rules")
    op.drop_table("profile_languages")
    op.drop_table("profile_skills")
    op.drop_table("skills")
    op.drop_index("uq_person_profile_owner", table_name="profiles")
    op.drop_table("profiles")
    op.drop_table("users")
