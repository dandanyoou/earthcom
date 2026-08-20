from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_DEVELOPMENT_JWT_SIGNING_KEY = "pangaea-local-development-signing-key"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://pangaea:pangaea-local-only@postgres:5432/pangaea"
    redis_url: str = "redis://redis:6379/0"
    frontend_origins: str = "http://localhost:3000"
    ai_mode: Literal["live", "replay", "stub"] = "stub"
    translate_provider: Literal["stub", "openai"] = "stub"
    openai_api_key: SecretStr = SecretStr("")
    openai_base_url: str = "https://api.openai.com/v1"
    pangaea_model_low: str = "gpt-4o-mini"
    ai_translate_max_expansion: float = 2.5
    ai_l3_min_confidence: float = 0.50
    ai_guard_min_confidence: float = 0.70
    trust_policy_version: str = "trust.v1"
    matching_policy_version: str = "matching.v1"
    deposit_cap_policy_version: str = "deposit-cap.v1"
    deposit_cap_amount_minor: int = 500_000
    deposit_provider: Literal["sandbox", "production"] = "sandbox"
    deposit_production_enabled: bool = False
    deposit_forfeiture_enabled: bool = False
    jwt_signing_key: SecretStr = SecretStr(LOCAL_DEVELOPMENT_JWT_SIGNING_KEY)
    rate_limit_pepper: SecretStr = SecretStr("pangaea-local-development-rate-limit-pepper")
    access_token_ttl_seconds: int = 900
    refresh_token_ttl_days: int = 30
    refresh_cookie_name: str = "pangaea_refresh"
    refresh_cookie_secure: bool = False

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        """Use psycopg's SQLAlchemy dialect for provider-issued Postgres URLs."""
        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @model_validator(mode="after")
    def validate_production_auth_settings(self) -> "Settings":
        if self.access_token_ttl_seconds != 900:
            raise ValueError("access token TTL must be 900 seconds")
        if self.app_env != "production":
            return self

        signing_key = self.jwt_signing_key.get_secret_value()
        if signing_key == LOCAL_DEVELOPMENT_JWT_SIGNING_KEY:
            raise ValueError(
                "production settings must not use the local development JWT signing key"
            )
        if len(signing_key.encode("utf-8")) < 32:
            raise ValueError("production JWT signing key must be at least 32 encoded bytes")
        if not self.refresh_cookie_secure:
            raise ValueError("production settings require secure refresh cookies")
        return self

    @property
    def frontend_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
