from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.errors import ProductError, register_error_handlers


async def test_product_error_uses_the_public_error_envelope() -> None:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/conflict")
    async def conflict() -> None:
        raise ProductError(
            code="VERSION_CONFLICT",
            message="The resource changed.",
            status_code=409,
            details={"expected_version": 3},
        )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/conflict")

    assert response.status_code == 409
    assert response.json() == {
        "ok": False,
        "error": {
            "code": "VERSION_CONFLICT",
            "message": "The resource changed.",
            "details": {"expected_version": 3},
        },
    }


async def test_unexpected_error_never_discloses_exception_text() -> None:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("database password must stay secret")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/unexpected")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "password" not in response.text
