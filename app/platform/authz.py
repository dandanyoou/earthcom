"""Request identity: bearer-token decoding plus the acting person profile.

Every protected route receives an Identity; object-level checks (conversation
membership, requester-only actions) happen in the domain queries themselves.
"""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.identity.models import User
from app.domains.profiles.models import Profile
from app.errors import ProductError
from app.platform.db import get_db_session
from app.settings import Settings, get_settings


@dataclass(frozen=True)
class Identity:
    user_id: UUID
    email: str
    locale: str
    profile_id: UUID | None
    profile: Profile | None


def _unauthorized() -> ProductError:
    return ProductError(
        code="AUTH_INVALID_CREDENTIALS",
        message="authentication required",
        status_code=401,
    )


def decode_access_token(token: str, settings: Settings) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_signing_key.get_secret_value(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc


async def get_identity(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> Identity:
    if not authorization or not authorization.startswith("Bearer "):
        raise _unauthorized()
    claims = decode_access_token(authorization.removeprefix("Bearer "), settings)
    try:
        user_id = UUID(str(claims["sub"]))
    except ValueError as exc:
        raise _unauthorized() from exc

    user = await session.get(User, user_id)
    if user is None or user.status != "ACTIVE":
        raise _unauthorized()
    if int(claims.get("token_version", 0)) != user.token_version:
        raise _unauthorized()

    profile = (
        await session.execute(
            select(Profile).where(
                Profile.owner_user_id == user_id,
                Profile.kind == "PERSON",
                Profile.status != "SUSPENDED",
            )
        )
    ).scalar_one_or_none()
    return Identity(
        user_id=user.id,
        email=user.email,
        locale=user.default_locale,
        profile_id=profile.id if profile else None,
        profile=profile,
    )


def require_profile(identity: Identity) -> Profile:
    if identity.profile is None or identity.profile.status != "ACTIVE":
        raise ProductError(
            code="PROFILE_NOT_ACTIVE",
            message="an active profile is required",
            status_code=422,
        )
    return identity.profile
