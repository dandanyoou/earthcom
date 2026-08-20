from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def test_live_does_not_depend_on_infrastructure() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "data": {"status": "live"},
        "meta": None,
    }


async def test_ready_confirms_database_redis_and_migration_head() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "data": {
            "status": "ready",
            "components": {
                "database": "ready",
                "redis": "ready",
                "migration": "ready",
            },
        },
        "meta": None,
    }
