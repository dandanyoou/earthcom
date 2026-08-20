import asyncio
import socket
from http.cookies import SimpleCookie
from typing import Any

from fastapi import Response
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from app.api.v1.auth import get_login_rate_limiter, set_refresh_cookie
from app.platform.rate_limit import SlidingWindowRateLimiter
from app.settings import Settings

PASSWORD = "correct horse battery staple"
AUTH_PATH = "/api/v1/auth"


def refresh_cookie_value(response, cookie_name: str) -> str:
    parsed = SimpleCookie()
    parsed.load(response.headers["set-cookie"])
    return parsed[cookie_name].value


async def post_with_refresh_cookie(
    environment: Any,
    path: str,
    refresh_token: str,
):
    async with AsyncClient(
        transport=ASGITransport(app=environment.app, raise_app_exceptions=False),
        base_url="http://test",
        cookies={environment.settings.refresh_cookie_name: refresh_token},
    ) as client:
        return await client.post(path)


async def test_register_returns_only_access_data_and_secure_cookie_contract(
    auth_environment: Any,
) -> None:
    response = await auth_environment.client.post(
        f"{AUTH_PATH}/register",
        json={
            "email": " Person@Example.COM ",
            "password": PASSWORD,
            "default_locale": "ko",
        },
    )

    assert response.status_code == 201
    assert response.json()["ok"] is True
    assert set(response.json()["data"]) == {
        "user_id",
        "access_token",
        "token_type",
        "expires_in",
    }
    assert response.json()["data"]["token_type"] == "Bearer"
    assert response.json()["data"]["expires_in"] == 900
    assert "refresh_token" not in response.text
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/api/v1/auth" in cookie
    assert "Max-Age=2592000" in cookie

    duplicate = await auth_environment.client.post(
        f"{AUTH_PATH}/register",
        json={
            "email": "person@example.com",
            "password": PASSWORD,
            "default_locale": "en",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "AUTH_EMAIL_ALREADY_REGISTERED"
    assert "person@example.com" not in duplicate.text


def test_refresh_cookie_is_secure_in_production() -> None:
    settings = Settings(
        app_env="production",
        jwt_signing_key="production-signing-key-with-at-least-32-bytes",
        refresh_cookie_secure=True,
    )
    response = Response()

    set_refresh_cookie(response, "opaque-token", settings)

    cookie = response.headers["set-cookie"]
    assert "Secure" in cookie
    assert "SameSite=none" in cookie


async def test_login_limits_the_socket_peer_and_ignores_forwarded_headers(
    auth_environment: Any,
) -> None:
    for attempt in range(10):
        response = await auth_environment.client.post(
            f"{AUTH_PATH}/login",
            headers={"x-forwarded-for": f"198.51.100.{attempt}"},
            json={"email": "absent@example.com", "password": PASSWORD},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"

    denied = await auth_environment.client.post(
        f"{AUTH_PATH}/login",
        headers={"x-forwarded-for": "203.0.113.200"},
        json={"email": "absent@example.com", "password": PASSWORD},
    )

    assert denied.status_code == 429
    assert denied.json()["error"]["code"] == "RATE_LIMITED"
    assert int(denied.headers["retry-after"]) > 0
    redis_keys = [
        key
        async for key in auth_environment.redis.scan_iter(
            match=f"{auth_environment.redis_prefix}:*"
        )
    ]
    assert len(redis_keys) == 1
    assert "127.0.0.1" not in redis_keys[0]
    assert "198.51.100" not in redis_keys[0]


async def test_production_server_disables_forwarded_peer_rewriting(
    auth_environment: Any,
) -> None:
    from app.server import create_server

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]
    server = create_server(auth_environment.app, host="127.0.0.1", port=port)
    server_task = asyncio.create_task(server.serve(sockets=[listener]))
    try:
        for _ in range(100):
            if server.started:
                break
            if server_task.done():
                await server_task
            await asyncio.sleep(0.01)
        else:
            raise AssertionError("Uvicorn did not start")

        async with AsyncClient(base_url=f"http://127.0.0.1:{port}") as client:
            for attempt in range(10):
                response = await client.post(
                    f"{AUTH_PATH}/login",
                    headers={"x-forwarded-for": f"198.51.100.{attempt}"},
                    json={"email": "absent@example.com", "password": PASSWORD},
                )
                assert response.status_code == 401

            denied = await client.post(
                f"{AUTH_PATH}/login",
                headers={"x-forwarded-for": "203.0.113.200"},
                json={"email": "absent@example.com", "password": PASSWORD},
            )

        assert denied.status_code == 429
        assert denied.json()["error"]["code"] == "RATE_LIMITED"
        assert int(denied.headers["retry-after"]) > 0
    finally:
        server.should_exit = True
        await server_task
        listener.close()


async def test_login_returns_only_access_data_and_the_refresh_cookie_contract(
    auth_environment: Any,
) -> None:
    await auth_environment.client.post(
        f"{AUTH_PATH}/register",
        json={
            "email": "person@example.com",
            "password": PASSWORD,
            "default_locale": "en",
        },
    )

    response = await auth_environment.client.post(
        f"{AUTH_PATH}/login",
        json={"email": "person@example.com", "password": PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["meta"] is None
    assert set(body["data"]) == {
        "user_id",
        "access_token",
        "token_type",
        "expires_in",
    }
    assert body["data"]["token_type"] == "Bearer"
    assert body["data"]["expires_in"] == 900
    assert "refresh_token" not in response.text
    assert refresh_cookie_value(response, auth_environment.settings.refresh_cookie_name)
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/api/v1/auth" in cookie
    assert "Max-Age=2592000" in cookie


async def test_refresh_reuse_revokes_the_replacement_token(
    auth_environment: Any,
) -> None:
    registered = await auth_environment.client.post(
        f"{AUTH_PATH}/register",
        json={
            "email": "person@example.com",
            "password": PASSWORD,
            "default_locale": "en",
        },
    )
    first_refresh = refresh_cookie_value(
        registered,
        auth_environment.settings.refresh_cookie_name,
    )

    rotated = await post_with_refresh_cookie(
        auth_environment,
        f"{AUTH_PATH}/refresh",
        first_refresh,
    )
    second_refresh = refresh_cookie_value(
        rotated,
        auth_environment.settings.refresh_cookie_name,
    )

    assert rotated.status_code == 200
    assert set(rotated.json()["data"]) == {
        "user_id",
        "access_token",
        "token_type",
        "expires_in",
    }
    assert "refresh_token" not in rotated.text
    assert second_refresh != first_refresh

    reused = await post_with_refresh_cookie(
        auth_environment,
        f"{AUTH_PATH}/refresh",
        first_refresh,
    )
    replacement = await post_with_refresh_cookie(
        auth_environment,
        f"{AUTH_PATH}/refresh",
        second_refresh,
    )

    assert reused.status_code == 401
    assert reused.json()["error"]["code"] == "AUTH_SESSION_REUSED"
    assert first_refresh not in reused.text
    assert replacement.status_code == 401
    assert replacement.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"
    assert second_refresh not in replacement.text


async def test_logout_is_idempotent_deletes_cookie_and_revokes_refresh(
    auth_environment: Any,
) -> None:
    registered = await auth_environment.client.post(
        f"{AUTH_PATH}/register",
        json={
            "email": "person@example.com",
            "password": PASSWORD,
            "default_locale": "en",
        },
    )
    refresh_token = refresh_cookie_value(
        registered,
        auth_environment.settings.refresh_cookie_name,
    )

    first_logout = await post_with_refresh_cookie(
        auth_environment,
        f"{AUTH_PATH}/logout",
        refresh_token,
    )
    second_logout = await auth_environment.client.post(f"{AUTH_PATH}/logout")
    rejected_refresh = await post_with_refresh_cookie(
        auth_environment,
        f"{AUTH_PATH}/refresh",
        refresh_token,
    )

    assert first_logout.status_code == 200
    assert second_logout.status_code == 200
    assert first_logout.json()["data"] == {}
    assert "Path=/api/v1/auth" in first_logout.headers["set-cookie"]
    assert "Max-Age=0" in first_logout.headers["set-cookie"]
    assert rejected_refresh.status_code == 401
    assert rejected_refresh.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


async def test_redis_failure_returns_a_fixed_dependency_error(
    auth_environment: Any,
) -> None:
    unavailable = Redis.from_url(
        "redis://127.0.0.1:1/0",
        decode_responses=True,
        socket_connect_timeout=0.05,
    )
    auth_environment.app.dependency_overrides[get_login_rate_limiter] = lambda: (
        SlidingWindowRateLimiter(unavailable, namespace=auth_environment.redis_prefix)
    )
    try:
        response = await auth_environment.client.post(
            f"{AUTH_PATH}/login",
            json={"email": "private@example.com", "password": PASSWORD},
        )
    finally:
        await unavailable.aclose()

    assert response.status_code == 503
    assert response.json() == {
        "ok": False,
        "error": {
            "code": "DEPENDENCY_UNAVAILABLE",
            "message": "A required dependency is unavailable.",
            "details": None,
        },
    }
    assert "127.0.0.1" not in response.text
    assert "private@example.com" not in response.text
