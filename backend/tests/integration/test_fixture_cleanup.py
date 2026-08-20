import psycopg
import pytest
from psycopg import sql
from sqlalchemy.engine import make_url

from app.settings import get_settings
from tests.integration.conftest import auth_environment as auth_environment_fixture


async def test_auth_fixture_drops_database_when_redis_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_body = auth_environment_fixture.__wrapped__
    environment_generator = fixture_body(monkeypatch)
    environment = await anext(environment_generator)
    test_url = make_url(environment.settings.database_url)
    database_name = test_url.database
    assert database_name is not None
    admin_url = test_url.set(drivername="postgresql", database="postgres")
    admin_connection_url = admin_url.render_as_string(hide_password=False)

    def fail_redis_scan(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("forced Redis cleanup failure")

    database_exists = True
    try:
        with monkeypatch.context() as cleanup_failure:
            cleanup_failure.setattr(environment.redis, "scan_iter", fail_redis_scan)
            with pytest.raises(RuntimeError, match="forced Redis cleanup failure"):
                await environment_generator.aclose()

        with psycopg.connect(admin_connection_url, autocommit=True) as connection:
            database_exists = (
                connection.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (database_name,),
                ).fetchone()
                is not None
            )

        assert database_exists is False
    finally:
        await environment.redis.aclose()
        get_settings.cache_clear()
        if database_exists:
            with psycopg.connect(admin_connection_url, autocommit=True) as connection:
                connection.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database_name))
                )
