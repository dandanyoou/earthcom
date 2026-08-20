import hashlib
import hmac
import time
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.identity.repository import SqlAlchemyAuthRepository
from app.domains.identity.schemas import IssuedAuth, LoginInput, RegisterInput
from app.domains.identity.service import AuthService
from app.domains.profiles.models import Profile
from app.envelope import SuccessEnvelope, ok
from app.errors import error_content
from app.platform.crypto import PasswordService
from app.platform.db import get_db_session
from app.platform.rate_limit import SlidingWindowRateLimiter
from app.platform.redis import get_redis
from app.settings import Settings, get_settings

AUTH_COOKIE_PATH = "/api/v1/auth"
LOGIN_RATE_LIMIT = 10
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 600

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class AccessTokenData(BaseModel):
    user_id: UUID
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        repository=SqlAlchemyAuthRepository(session),
        password_service=PasswordService(),
        settings=settings,
    )


def get_login_rate_limiter(
    redis: Annotated[Redis, Depends(get_redis)],
) -> SlidingWindowRateLimiter:
    return SlidingWindowRateLimiter(redis, namespace="pangaea:auth:login")


def rate_limit_key(peer_ip: str, settings: Settings) -> str:
    digest = hmac.new(
        settings.rate_limit_pepper.get_secret_value().encode("utf-8"),
        peer_ip.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"ip:{digest}"


def set_refresh_cookie(response: Response, refresh_token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=settings.refresh_token_ttl_days * 86400,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="none" if settings.refresh_cookie_secure else "lax",
        path=AUTH_COOKIE_PATH,
    )


def delete_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=AUTH_COOKIE_PATH,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite="none" if settings.refresh_cookie_secure else "lax",
    )


def access_data(issued: IssuedAuth) -> AccessTokenData:
    return AccessTokenData(
        user_id=issued.user_id,
        access_token=issued.access_token,
        expires_in=issued.expires_in,
    )


@router.post(
    "/register",
    response_model=SuccessEnvelope[AccessTokenData],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    submitted: RegisterInput,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessEnvelope[AccessTokenData]:
    issued = await service.register(
        str(submitted.email),
        submitted.password,
        submitted.default_locale,
        datetime.now(UTC),
    )
    # Every account gets a person profile immediately; S07 fills it in.
    display_name = str(submitted.email).split("@")[0][:80] or "새 사용자"
    session.add(
        Profile(
            kind="PERSON",
            owner_user_id=issued.user_id,
            display_name=display_name,
            locale=submitted.default_locale,
            timezone="Asia/Seoul",
            status="ACTIVE",
        )
    )
    await session.commit()
    set_refresh_cookie(response, issued.refresh_token, settings)
    return ok(access_data(issued))


@router.post(
    "/login",
    response_model=SuccessEnvelope[AccessTokenData],
    status_code=status.HTTP_200_OK,
)
async def login(
    submitted: LoginInput,
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    limiter: Annotated[SlidingWindowRateLimiter, Depends(get_login_rate_limiter)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessEnvelope[AccessTokenData] | JSONResponse:
    peer_ip = request.client.host if request.client is not None else ""
    decision = await limiter.check(
        rate_limit_key(peer_ip, settings),
        limit=LOGIN_RATE_LIMIT,
        window_seconds=LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        now_ms=time.time_ns() // 1_000_000,
    )
    if not decision.allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_content("RATE_LIMITED", "Too many login attempts."),
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )

    issued = await service.login(
        str(submitted.email),
        submitted.password,
        datetime.now(UTC),
    )
    set_refresh_cookie(response, issued.refresh_token, settings)
    return ok(access_data(issued))


@router.post(
    "/refresh",
    response_model=SuccessEnvelope[AccessTokenData],
    status_code=status.HTTP_200_OK,
)
async def refresh(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessEnvelope[AccessTokenData]:
    refresh_token = request.cookies.get(settings.refresh_cookie_name, "")
    issued = await service.refresh(refresh_token, datetime.now(UTC))
    set_refresh_cookie(response, issued.refresh_token, settings)
    return ok(access_data(issued))


@router.post(
    "/logout",
    response_model=SuccessEnvelope[dict[str, object]],
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessEnvelope[dict[str, object]]:
    await service.logout(
        request.cookies.get(settings.refresh_cookie_name),
        datetime.now(UTC),
    )
    delete_refresh_cookie(response, settings)
    return ok({})
