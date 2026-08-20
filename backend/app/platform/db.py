from collections.abc import AsyncIterator
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.settings import get_settings

# Resolved at import time so both the container (/app) and a native checkout
# find the same alembic.ini without touching the filesystem inside a coroutine.
ALEMBIC_CONFIG_PATH = Path(__file__).resolve().parents[2] / "alembic.ini"


async def get_db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            yield session
    finally:
        await engine.dispose()


async def check_database() -> None:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    finally:
        await engine.dispose()


async def check_migration_head() -> None:
    config_path = ALEMBIC_CONFIG_PATH
    alembic_config = Config(str(config_path))
    alembic_config.set_main_option("script_location", str(config_path.parent / "migrations"))
    expected = ScriptDirectory.from_config(alembic_config).get_current_head()

    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            version_table = await connection.scalar(text("SELECT to_regclass('alembic_version')"))
            current = None
            if version_table is not None:
                current = await connection.scalar(text("SELECT version_num FROM alembic_version"))
    finally:
        await engine.dispose()

    if current != expected:
        raise RuntimeError("database migration revision does not match application head")
