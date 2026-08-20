from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import jwt
import pytest

from app.platform.crypto import (
    PasswordService,
    hash_refresh_token,
    issue_access_token,
    new_refresh_token,
)
from app.settings import Settings

USER_ID = UUID("018ec1fe-9d5c-7b96-bc1b-0a8d7a5b3f01")
SESSION_ID = UUID("018ec1fe-9d5c-7b96-bc1b-0a8d7a5b3f02")
NOW = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_signing_key="test-signing-key-with-at-least-32b",
        rate_limit_pepper="test-rate-limit-pepper",
    )


def test_password_hash_is_argon2id_and_verifies_without_echoing_secret() -> None:
    encoded = PasswordService().hash("a-secure-password")

    assert encoded.startswith("$argon2id$")
    assert "a-secure-password" not in encoded
    assert PasswordService().verify(encoded, "a-secure-password") is True
    assert PasswordService().verify(encoded, "wrong-password") is False


def test_refresh_tokens_are_url_safe_and_hashed_with_sha256() -> None:
    token = new_refresh_token()

    assert len(token) >= 64
    assert hash_refresh_token("refresh-token") == (
        "0eb17643d4e9261163783a420859c92c7d212fa9624106a12b510afbec266120"
    )
    assert hash_refresh_token(token) != token


def test_access_token_has_only_allowed_product_claims(settings: Settings) -> None:
    token = issue_access_token(
        user_id=USER_ID,
        session_id=SESSION_ID,
        token_version=2,
        now=NOW,
        settings=settings,
    )

    claims = jwt.decode(
        token,
        settings.jwt_signing_key.get_secret_value(),
        algorithms=["HS256"],
        options={"verify_exp": False},
    )
    assert set(claims) == {"sub", "session_id", "token_version", "iat", "exp"}
    assert claims["sub"] == str(USER_ID)
    assert claims["session_id"] == str(SESSION_ID)
    assert claims["token_version"] == 2
    assert claims["exp"] - claims["iat"] == 900


def test_production_settings_reject_local_key_and_insecure_refresh_cookie() -> None:
    with pytest.raises(ValueError, match="local development JWT signing key"):
        Settings(
            app_env="production",
            jwt_signing_key="pangaea-local-development-signing-key",
            rate_limit_pepper="production-rate-limit-pepper",
            refresh_cookie_secure=True,
        )

    with pytest.raises(ValueError, match="secure refresh cookies"):
        Settings(
            app_env="production",
            jwt_signing_key="production-signing-key-with-at-least-32-bytes",
            rate_limit_pepper="production-rate-limit-pepper",
            refresh_cookie_secure=False,
        )


@pytest.mark.parametrize(
    "weak_key",
    [
        "",
        "private-short-signing-key",
        "é" * 15,
    ],
)
def test_production_settings_reject_jwt_keys_shorter_than_32_encoded_bytes(
    weak_key: str,
) -> None:
    with pytest.raises(ValueError, match="at least 32 encoded bytes") as invalid:
        Settings(
            app_env="production",
            jwt_signing_key=weak_key,
            rate_limit_pepper="production-rate-limit-pepper",
            refresh_cookie_secure=True,
        )

    if weak_key:
        assert weak_key not in str(invalid.value)


def test_production_settings_measure_jwt_key_length_in_encoded_bytes() -> None:
    settings = Settings(
        app_env="production",
        jwt_signing_key="é" * 16,
        rate_limit_pepper="production-rate-limit-pepper",
        refresh_cookie_secure=True,
    )

    assert settings.jwt_signing_key.get_secret_value() == "é" * 16


def test_access_token_rejects_naive_time_and_preserves_an_aware_utc_instant(
    settings: Settings,
) -> None:
    with pytest.raises(ValueError, match="authentication time must be timezone-aware"):
        issue_access_token(
            user_id=USER_ID,
            session_id=SESSION_ID,
            token_version=2,
            now=NOW.replace(tzinfo=None),
            settings=settings,
        )

    offset_now = NOW.astimezone(timezone(timedelta(hours=9)))
    token = issue_access_token(
        user_id=USER_ID,
        session_id=SESSION_ID,
        token_version=2,
        now=offset_now,
        settings=settings,
    )
    claims = jwt.decode(
        token,
        settings.jwt_signing_key.get_secret_value(),
        algorithms=["HS256"],
        options={"verify_exp": False},
    )
    assert claims["iat"] == int(NOW.timestamp())
    assert claims["exp"] == int((NOW + timedelta(seconds=900)).timestamp())


def test_settings_reject_non_900_access_token_ttl_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACCESS_TOKEN_TTL_SECONDS", "901")

    with pytest.raises(ValueError, match="access token TTL must be 900 seconds"):
        Settings(
            jwt_signing_key="test-signing-key-with-at-least-32b",
            rate_limit_pepper="test-rate-limit-pepper",
        )
