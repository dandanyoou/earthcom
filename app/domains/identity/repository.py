from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.identity.models import AuthSession, PasswordCredential, RefreshToken, User
from app.domains.identity.schemas import (
    LoginIdentity,
    RotationOutcome,
    RotationStatus,
    SessionIdentity,
)


class DuplicateEmailError(Exception):
    pass


class AuthRepository(Protocol):
    async def find_login_identity(self, email: str) -> LoginIdentity | None: ...

    async def create_identity(
        self,
        *,
        email: str,
        password_hash: str,
        default_locale: str,
    ) -> LoginIdentity: ...

    async def create_session(
        self,
        *,
        user_id: UUID,
        token_version: int,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> SessionIdentity | None: ...

    async def rotate_refresh(
        self,
        *,
        refresh_token_hash: str,
        replacement_token_hash: str,
        replacement_expires_at: datetime,
        now: datetime,
    ) -> RotationOutcome: ...

    async def revoke_refresh_family(
        self,
        *,
        refresh_token_hash: str,
        now: datetime,
    ) -> None: ...


class SqlAlchemyAuthRepository:
    """Own transactions and lock applicable rows User -> AuthSession -> RefreshToken.

    Discovery reads are non-authoritative; locked rows and relationships are revalidated.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_login_identity(self, email: str) -> LoginIdentity | None:
        async with self._session.begin():
            row = (
                await self._session.execute(
                    select(User, PasswordCredential)
                    .join(PasswordCredential, PasswordCredential.user_id == User.id)
                    .where(User.email == email)
                )
            ).one_or_none()
            if row is None:
                return None
            user, credential = row
            identity = LoginIdentity(
                user_id=user.id,
                password_hash=credential.password_hash,
                status=user.status,
                token_version=user.token_version,
            )
        return identity

    async def create_identity(
        self,
        *,
        email: str,
        password_hash: str,
        default_locale: str,
    ) -> LoginIdentity:
        try:
            async with self._session.begin():
                user = User(
                    email=email,
                    status="ACTIVE",
                    default_locale=default_locale,
                    token_version=1,
                )
                self._session.add(user)
                await self._session.flush()
                self._session.add(PasswordCredential(user_id=user.id, password_hash=password_hash))
                identity = LoginIdentity(
                    user_id=user.id,
                    password_hash=password_hash,
                    status=user.status,
                    token_version=user.token_version,
                )
        except IntegrityError as exc:
            raise DuplicateEmailError from exc
        return identity

    async def create_session(
        self,
        *,
        user_id: UUID,
        token_version: int,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> SessionIdentity | None:
        async with self._session.begin():
            user = (
                await self._session.execute(
                    select(User.id, User.status, User.token_version)
                    .where(User.id == user_id)
                    .with_for_update()
                )
            ).one_or_none()
            if user is None:
                return None
            locked_user_id, status, current_token_version = user
            if status != "ACTIVE" or current_token_version != token_version:
                return None
            auth_session = AuthSession(
                user_id=locked_user_id,
                token_version=current_token_version,
                expires_at=expires_at,
            )
            self._session.add(auth_session)
            await self._session.flush()
            self._session.add(
                RefreshToken(
                    session_id=auth_session.id,
                    token_hash=refresh_token_hash,
                    expires_at=expires_at,
                )
            )
            identity = SessionIdentity(
                user_id=locked_user_id,
                session_id=auth_session.id,
                token_version=current_token_version,
            )
        return identity

    async def rotate_refresh(
        self,
        *,
        refresh_token_hash: str,
        replacement_token_hash: str,
        replacement_expires_at: datetime,
        now: datetime,
    ) -> RotationOutcome:
        async with self._session.begin():
            submitted_token = (
                await self._session.execute(
                    select(RefreshToken.id, RefreshToken.session_id, AuthSession.user_id)
                    .join(AuthSession, AuthSession.id == RefreshToken.session_id)
                    .where(RefreshToken.token_hash == refresh_token_hash)
                )
            ).one_or_none()
            if submitted_token is None:
                outcome = RotationOutcome(status=RotationStatus.INVALID)
            else:
                token_id, session_id, user_id = submitted_token
                user = (
                    await self._session.execute(
                        select(User.id, User.status, User.token_version)
                        .where(User.id == user_id)
                        .with_for_update()
                    )
                ).one_or_none()
                auth_session = await self._session.scalar(
                    select(AuthSession)
                    .where(
                        AuthSession.id == session_id,
                        AuthSession.user_id == user_id,
                    )
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
                refresh = await self._session.scalar(
                    select(RefreshToken)
                    .where(
                        RefreshToken.id == token_id,
                        RefreshToken.session_id == session_id,
                    )
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
                if user is None or auth_session is None or refresh is None:
                    return RotationOutcome(status=RotationStatus.INVALID)
                locked_user_id, status, current_token_version = user
                family_invalid = (
                    refresh.expires_at <= now
                    or refresh.revoked_at is not None
                    or auth_session.expires_at <= now
                    or auth_session.revoked_at is not None
                    or status != "ACTIVE"
                    or auth_session.token_version != current_token_version
                )
                if family_invalid:
                    outcome = RotationOutcome(status=RotationStatus.INVALID)
                elif refresh.consumed_at is not None:
                    await self._revoke_session(
                        auth_session,
                        now=now,
                        reason="REFRESH_TOKEN_REUSE",
                    )
                    outcome = RotationOutcome(status=RotationStatus.REUSED)
                else:
                    replacement = RefreshToken(
                        session_id=auth_session.id,
                        token_hash=replacement_token_hash,
                        expires_at=min(replacement_expires_at, auth_session.expires_at),
                    )
                    self._session.add(replacement)
                    await self._session.flush()
                    refresh.consumed_at = now
                    refresh.replaced_by_token_id = replacement.id
                    outcome = RotationOutcome(
                        status=RotationStatus.ROTATED,
                        user_id=locked_user_id,
                        session_id=auth_session.id,
                        token_version=auth_session.token_version,
                    )
        return outcome

    async def revoke_refresh_family(
        self,
        *,
        refresh_token_hash: str,
        now: datetime,
    ) -> None:
        async with self._session.begin():
            submitted_token = (
                await self._session.execute(
                    select(RefreshToken.id, RefreshToken.session_id, AuthSession.user_id)
                    .join(AuthSession, AuthSession.id == RefreshToken.session_id)
                    .where(RefreshToken.token_hash == refresh_token_hash)
                )
            ).one_or_none()
            if submitted_token is None:
                return
            token_id, session_id, user_id = submitted_token
            locked_user_id = await self._session.scalar(
                select(User.id).where(User.id == user_id).with_for_update()
            )
            auth_session = await self._session.scalar(
                select(AuthSession)
                .where(
                    AuthSession.id == session_id,
                    AuthSession.user_id == user_id,
                )
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            refresh = await self._session.scalar(
                select(RefreshToken)
                .where(
                    RefreshToken.id == token_id,
                    RefreshToken.session_id == session_id,
                )
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if locked_user_id is None or auth_session is None or refresh is None:
                return
            await self._revoke_session(auth_session, now=now, reason="LOGOUT")

    async def _revoke_session(
        self,
        auth_session: AuthSession,
        *,
        now: datetime,
        reason: str,
    ) -> None:
        if auth_session.revoked_at is None:
            auth_session.revoked_at = now
            auth_session.revocation_reason = reason
        await self._session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.session_id == auth_session.id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
