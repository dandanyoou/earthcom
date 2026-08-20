from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.settings import get_settings


@dataclass(frozen=True)
class RepositoryDatabase:
    engine: AsyncEngine
    sessions: async_sessionmaker[AsyncSession]


@pytest.fixture
def migrated_database_url(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    configured = make_url(get_settings().database_url)
    database_name = f"pangaea_repository_{uuid4().hex}"
    admin_url = configured.set(drivername="postgresql", database="postgres")
    test_url = configured.set(database=database_name)

    with psycopg.connect(
        admin_url.render_as_string(hide_password=False),
        autocommit=True,
    ) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    rendered_url = test_url.render_as_string(hide_password=False)
    monkeypatch.setenv("DATABASE_URL", rendered_url)
    get_settings.cache_clear()
    try:
        command.upgrade(Config("alembic.ini"), "head")
        yield rendered_url
    finally:
        get_settings.cache_clear()
        with psycopg.connect(
            admin_url.render_as_string(hide_password=False),
            autocommit=True,
        ) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database_name))
            )


@pytest.fixture
async def repository_database(
    migrated_database_url: str,
) -> AsyncIterator[RepositoryDatabase]:
    engine = create_async_engine(migrated_database_url)
    try:
        yield RepositoryDatabase(
            engine=engine,
            sessions=async_sessionmaker(engine, expire_on_commit=False),
        )
    finally:
        await engine.dispose()
