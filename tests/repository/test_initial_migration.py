from collections.abc import Iterator
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url

from app.settings import get_settings

DOMAIN_TABLES = {
    "auth_sessions",
    "availability_rules",
    "password_credentials",
    "profile_languages",
    "profile_skills",
    "profiles",
    "refresh_tokens",
    "skills",
    "users",
}


def column_names(database: object, table_name: str) -> set[str]:
    return {column["name"] for column in database.get_columns(table_name)}


@pytest.fixture
def empty_database_url(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    configured = make_url(get_settings().database_url)
    database_name = f"pangaea_test_{uuid4().hex}"
    admin_url = configured.set(drivername="postgresql", database="postgres")
    test_url = configured.set(database=database_name)

    admin_connection_url = admin_url.render_as_string(hide_password=False)
    with psycopg.connect(admin_connection_url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    monkeypatch.setenv("DATABASE_URL", test_url.render_as_string(hide_password=False))
    get_settings.cache_clear()
    try:
        yield test_url.render_as_string(hide_password=False)
    finally:
        get_settings.cache_clear()
        with psycopg.connect(
            admin_url.render_as_string(hide_password=False), autocommit=True
        ) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database_name))
            )


def test_initial_migration_upgrades_and_downgrades_empty_database(
    empty_database_url: str,
) -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "head")

    engine = create_engine(empty_database_url)
    try:
        database = inspect(engine)
        upgraded_tables = set(database.get_table_names())
        assert DOMAIN_TABLES | {"alembic_version"} <= upgraded_tables

        user_columns = {column["name"]: column for column in database.get_columns("users")}
        token_version = user_columns["token_version"]
        assert token_version["nullable"] is False
        assert token_version["default"] is not None
        assert token_version["default"].split("::", maxsplit=1)[0].strip("'") == "1"
        assert any(
            "token_version > 0" in constraint["sqltext"]
            for constraint in database.get_check_constraints("users")
        )

        assert column_names(database, "password_credentials") == {
            "user_id",
            "password_hash",
            "created_at",
            "updated_at",
        }
        assert column_names(database, "auth_sessions") == {
            "id",
            "user_id",
            "token_version",
            "expires_at",
            "revoked_at",
            "revocation_reason",
            "created_at",
            "updated_at",
        }
        assert column_names(database, "refresh_tokens") == {
            "id",
            "session_id",
            "token_hash",
            "expires_at",
            "consumed_at",
            "revoked_at",
            "replaced_by_token_id",
            "created_at",
        }
        assert ["token_hash"] in [
            constraint["column_names"]
            for constraint in database.get_unique_constraints("refresh_tokens")
        ]

        auth_session_indexes = {
            tuple(index["column_names"]) for index in database.get_indexes("auth_sessions")
        }
        refresh_token_indexes = {
            tuple(index["column_names"]) for index in database.get_indexes("refresh_tokens")
        }
        assert ("user_id", "revoked_at") in auth_session_indexes
        assert ("session_id", "revoked_at") in refresh_token_indexes

        def foreign_key_details(table_name: str) -> set[tuple[str, str, str]]:
            return {
                (
                    foreign_key["constrained_columns"][0],
                    foreign_key["referred_table"],
                    foreign_key["options"]["ondelete"],
                )
                for foreign_key in database.get_foreign_keys(table_name)
            }

        assert foreign_key_details("password_credentials") == {("user_id", "users", "CASCADE")}
        assert foreign_key_details("auth_sessions") == {("user_id", "users", "CASCADE")}
        assert foreign_key_details("refresh_tokens") == {
            ("session_id", "auth_sessions", "CASCADE"),
            ("replaced_by_token_id", "refresh_tokens", "SET NULL"),
        }

        with engine.connect() as connection:
            extensions = set(
                connection.exec_driver_sql(
                    "SELECT extname FROM pg_extension WHERE extname IN ('citext', 'vector')"
                ).scalars()
            )
        assert extensions == {"citext", "vector"}
    finally:
        engine.dispose()

    command.downgrade(config, "base")

    engine = create_engine(empty_database_url)
    try:
        downgraded_tables = set(inspect(engine).get_table_names())
        assert DOMAIN_TABLES.isdisjoint(downgraded_tables)
    finally:
        engine.dispose()
