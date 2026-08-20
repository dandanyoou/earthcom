from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from psycopg import sql
from redis.asyncio import Redis
from sqlalchemy.engine import make_url

from app.api.v1.auth import get_login_rate_limiter
from app.main import create_app
from app.platform.rate_limit import SlidingWindowRateLimiter
from app.settings import Settings, get_settings


@dataclass(frozen=True)
class AuthTestEnvironment:
    app: FastAPI
    client: AsyncClient
    redis: Redis
    redis_prefix: str
    settings: Settings


@pytest.fixture
async def auth_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[AuthTestEnvironment]:
    configured = make_url(get_settings().database_url)
    database_name = f"pangaea_auth_api_{uuid4().hex}"
    admin_url = configured.set(drivername="postgresql", database="postgres")
    test_url = configured.set(database=database_name)
    rendered_test_url = test_url.render_as_string(hide_password=False)

    with psycopg.connect(
        admin_url.render_as_string(hide_password=False),
        autocommit=True,
    ) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    monkeypatch.setenv("DATABASE_URL", rendered_test_url)
    get_settings.cache_clear()
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    redis_prefix = f"test:auth-api:{uuid4().hex}"

    try:
        command.upgrade(Config("alembic.ini"), "head")
        limiter = SlidingWindowRateLimiter(redis, namespace=redis_prefix)
        app = create_app()
        app.dependency_overrides[get_login_rate_limiter] = lambda: limiter
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            yield AuthTestEnvironment(
                app=app,
                client=client,
                redis=redis,
                redis_prefix=redis_prefix,
                settings=get_settings(),
            )
    finally:
        try:
            try:
                keys = [key async for key in redis.scan_iter(match=f"{redis_prefix}:*")]
                if keys:
                    await redis.delete(*keys)
            finally:
                await redis.aclose()
        finally:
            get_settings.cache_clear()
            with psycopg.connect(
                admin_url.render_as_string(hide_password=False),
                autocommit=True,
            ) as connection:
                connection.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database_name))
                )
