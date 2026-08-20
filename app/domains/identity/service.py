from datetime import datetime, timedelta

from pydantic import ValidationError

from app.domains.identity.repository import AuthRepository, DuplicateEmailError
from app.domains.identity.schemas import (
    IssuedAuth,
    LoginIdentity,
    LoginInput,
    RegisterInput,
    RotationStatus,
    SessionIdentity,
)
from app.errors import ProductError
from app.platform.crypto import (
    PasswordService,
    hash_refresh_token,
    issue_access_token,
    new_refresh_token,
    normalize_auth_time,
)
from app.settings import Settings

INVALID_CREDENTIALS_MESSAGE = "invalid credentials"
DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "l3GaQBJun85uKUX4eje0Jg$fX4G1jucuwe1Js5lEGF+Q/gaoIp3JSFKssb26fPaS7c"
)


class AuthService:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        password_service: PasswordService,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._password_service = password_service
        self._settings = settings

    async def register(
        self,
        email: str,
        password: str,
        default_locale: str,
        now: datetime,
    ) -> IssuedAuth:
        now = normalize_auth_time(now)
        try:
            submitted = RegisterInput(
                email=email,
                password=password,
                default_locale=default_locale,
            )
        except ValidationError:
            raise self._invalid_input() from None
        try:
            identity = await self._repository.create_identity(
                email=str(submitted.email),
                password_hash=self._password_service.hash(submitted.password),
                default_locale=submitted.default_locale,
            )
        except DuplicateEmailError as exc:
            raise ProductError(
                code="AUTH_EMAIL_ALREADY_REGISTERED",
                message="email is already registered",
                status_code=409,
            ) from exc
        return await self._issue_session(identity, now)

    async def login(self, email: str, password: str, now: datetime) -> IssuedAuth:
        now = normalize_auth_time(now)
        try:
            submitted = LoginInput(email=email, password=password)
        except ValidationError:
            raise self._invalid_input() from None
        identity = await self._repository.find_login_identity(str(submitted.email))
        candidate_hash = identity.password_hash if identity is not None else DUMMY_PASSWORD_HASH
        password_valid = self._password_service.verify(
            candidate_hash,
            submitted.password,
        )
        if identity is None or identity.status != "ACTIVE" or not password_valid:
            raise self._invalid_credentials()
        return await self._issue_session(identity, now)

    async def refresh(self, refresh_token: str, now: datetime) -> IssuedAuth:
        now = normalize_auth_time(now)
        replacement_token = new_refresh_token()
        outcome = await self._repository.rotate_refresh(
            refresh_token_hash=hash_refresh_token(refresh_token),
            replacement_token_hash=hash_refresh_token(replacement_token),
            replacement_expires_at=self._refresh_expiry(now),
            now=now,
        )
        if outcome.status is RotationStatus.REUSED:
            raise ProductError(
                code="AUTH_SESSION_REUSED",
                message="refresh token reuse detected",
                status_code=401,
            )
        if (
            outcome.status is not RotationStatus.ROTATED
            or outcome.user_id is None
            or outcome.session_id is None
            or outcome.token_version is None
        ):
            raise self._invalid_credentials()
        return IssuedAuth(
            user_id=outcome.user_id,
            access_token=issue_access_token(
                user_id=outcome.user_id,
                session_id=outcome.session_id,
                token_version=outcome.token_version,
                now=now,
                settings=self._settings,
            ),
            refresh_token=replacement_token,
            expires_in=self._settings.access_token_ttl_seconds,
        )

    async def logout(self, refresh_token: str | None, now: datetime) -> None:
        now = normalize_auth_time(now)
        if not refresh_token:
            return
        await self._repository.revoke_refresh_family(
            refresh_token_hash=hash_refresh_token(refresh_token),
            now=now,
        )

    async def _issue_session(self, identity: LoginIdentity, now: datetime) -> IssuedAuth:
        refresh_token = new_refresh_token()
        session = await self._repository.create_session(
            user_id=identity.user_id,
            token_version=identity.token_version,
            refresh_token_hash=hash_refresh_token(refresh_token),
            expires_at=self._refresh_expiry(now),
        )
        if session is None:
            raise self._invalid_credentials()
        return self._issued_auth(session, refresh_token, now)

    def _issued_auth(
        self,
        session: SessionIdentity,
        refresh_token: str,
        now: datetime,
    ) -> IssuedAuth:
        return IssuedAuth(
            user_id=session.user_id,
            access_token=issue_access_token(
                user_id=session.user_id,
                session_id=session.session_id,
                token_version=session.token_version,
                now=now,
                settings=self._settings,
            ),
            refresh_token=refresh_token,
            expires_in=self._settings.access_token_ttl_seconds,
        )

    def _refresh_expiry(self, now: datetime) -> datetime:
        return now + timedelta(days=self._settings.refresh_token_ttl_days)

    @staticmethod
    def _invalid_credentials() -> ProductError:
        return ProductError(
            code="AUTH_INVALID_CREDENTIALS",
            message=INVALID_CREDENTIALS_MESSAGE,
            status_code=401,
        )

    @staticmethod
    def _invalid_input() -> ProductError:
        return ProductError(
            code="VALIDATION_ERROR",
            message="invalid authentication input",
            status_code=422,
        )
