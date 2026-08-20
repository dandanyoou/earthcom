from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
import pytest

from app.domains.identity.repository import DuplicateEmailError
from app.domains.identity.schemas import (
    LoginIdentity,
    RotationOutcome,
    RotationStatus,
    SessionIdentity,
)
from app.domains.identity.service import AuthService
from app.errors import ProductError
from app.platform.crypto import PasswordService
from app.settings import Settings

PASSWORD = "correct horse battery staple"
NOW = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)


@dataclass
class FakeUser:
    user_id: UUID
    password_hash: str
    status: str
    token_version: int


@dataclass
class FakeSession:
    user_id: UUID
    token_version: int
    revoked: bool = False


@dataclass
class FakeRefreshToken:
    session_id: UUID
    consumed: bool = False
    revoked: bool = False


class InMemoryAuthRepository:
    def __init__(self) -> None:
        self.users: dict[str, FakeUser] = {}
        self.sessions: dict[UUID, FakeSession] = {}
        self.refresh_tokens: dict[str, FakeRefreshToken] = {}
        self.last_session_expires_at: datetime | None = None
        self.last_rotation_now: datetime | None = None
        self.last_rotation_expires_at: datetime | None = None
        self.last_revocation_now: datetime | None = None
        self.reject_session_creation = False

    async def find_login_identity(self, email: str) -> LoginIdentity | None:
        user = self.users.get(email)
        if user is None:
            return None
        return LoginIdentity(
            user_id=user.user_id,
            password_hash=user.password_hash,
            status=user.status,
            token_version=user.token_version,
        )

    async def create_identity(
        self,
        *,
        email: str,
        password_hash: str,
        default_locale: str,
    ) -> LoginIdentity:
        del default_locale
        if email in self.users:
            raise DuplicateEmailError
        user = FakeUser(
            user_id=uuid4(),
            password_hash=password_hash,
            status="ACTIVE",
            token_version=1,
        )
        self.users[email] = user
        return LoginIdentity(
            user_id=user.user_id,
            password_hash=user.password_hash,
            status=user.status,
            token_version=user.token_version,
        )

    async def create_session(
        self,
        *,
        user_id: UUID,
        token_version: int,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> SessionIdentity | None:
        self.last_session_expires_at = expires_at
        if self.reject_session_creation:
            return None
        session_id = uuid4()
        self.sessions[session_id] = FakeSession(
            user_id=user_id,
            token_version=token_version,
        )
        self.refresh_tokens[refresh_token_hash] = FakeRefreshToken(session_id=session_id)
        return SessionIdentity(
            user_id=user_id,
            session_id=session_id,
            token_version=token_version,
        )

    async def rotate_refresh(
        self,
        *,
        refresh_token_hash: str,
        replacement_token_hash: str,
        replacement_expires_at: datetime,
        now: datetime,
    ) -> RotationOutcome:
        self.last_rotation_now = now
        self.last_rotation_expires_at = replacement_expires_at
        token = self.refresh_tokens.get(refresh_token_hash)
        if token is None:
            return RotationOutcome(status=RotationStatus.INVALID)
        session = self.sessions[token.session_id]
        user = self._user_by_id(session.user_id)
        if (
            token.revoked
            or session.revoked
            or user.status != "ACTIVE"
            or session.token_version != user.token_version
        ):
            return RotationOutcome(status=RotationStatus.INVALID)
        if token.consumed:
            session.revoked = True
            for family_token in self.refresh_tokens.values():
                if family_token.session_id == token.session_id:
                    family_token.revoked = True
            return RotationOutcome(status=RotationStatus.REUSED)

        token.consumed = True
        self.refresh_tokens[replacement_token_hash] = FakeRefreshToken(session_id=token.session_id)
        return RotationOutcome(
            status=RotationStatus.ROTATED,
            user_id=user.user_id,
            session_id=token.session_id,
            token_version=user.token_version,
        )

    async def revoke_refresh_family(self, *, refresh_token_hash: str, now: datetime) -> None:
        self.last_revocation_now = now
        token = self.refresh_tokens.get(refresh_token_hash)
        if token is None:
            return
        session = self.sessions[token.session_id]
        session.revoked = True
        for family_token in self.refresh_tokens.values():
            if family_token.session_id == token.session_id:
                family_token.revoked = True

    def deactivate(self, email: str) -> None:
        self.users[email].status = "SUSPENDED"

    def _user_by_id(self, user_id: UUID) -> FakeUser:
        return next(user for user in self.users.values() if user.user_id == user_id)


@pytest.fixture
def repository() -> InMemoryAuthRepository:
    return InMemoryAuthRepository()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_signing_key="test-signing-key-with-at-least-32b",
        rate_limit_pepper="test-rate-limit-pepper",
    )


@pytest.fixture
def service(repository: InMemoryAuthRepository, settings: Settings) -> AuthService:
    return AuthService(
        repository=repository,
        password_service=PasswordService(),
        settings=settings,
    )


def decode_access_token(token: str, settings: Settings) -> dict[str, object]:
    return jwt.decode(
        token,
        settings.jwt_signing_key.get_secret_value(),
        algorithms=["HS256"],
        options={"verify_exp": False},
    )


def repository_state(repository: InMemoryAuthRepository) -> tuple[object, ...]:
    return (
        {
            (email, user.user_id, user.status, user.token_version)
            for email, user in repository.users.items()
        },
        {
            (session_id, session.user_id, session.token_version, session.revoked)
            for session_id, session in repository.sessions.items()
        },
        {
            (token_hash, token.session_id, token.consumed, token.revoked)
            for token_hash, token in repository.refresh_tokens.items()
        },
    )


async def test_register_normalizes_email_and_issues_a_session(
    service: AuthService,
    settings: Settings,
) -> None:
    registered = await service.register(" Person@Example.COM ", PASSWORD, "ko", NOW)
    logged_in = await service.login("person@example.com", PASSWORD, NOW)

    claims = decode_access_token(registered.access_token, settings)
    assert logged_in.user_id == registered.user_id
    assert claims["sub"] == str(registered.user_id)
    assert registered.refresh_token != logged_in.refresh_token
    assert registered.expires_in == 900


async def test_register_rejects_a_case_insensitive_duplicate_email(
    service: AuthService,
) -> None:
    await service.register("person@example.com", PASSWORD, "en", NOW)

    with pytest.raises(ProductError) as duplicate:
        await service.register("PERSON@example.com", PASSWORD, "en", NOW)

    assert duplicate.value.code == "AUTH_EMAIL_ALREADY_REGISTERED"
    assert duplicate.value.status_code == 409
    assert "PERSON@example.com" not in duplicate.value.message


async def test_login_uses_one_generic_failure_for_absent_wrong_and_inactive_users(
    service: AuthService,
    repository: InMemoryAuthRepository,
) -> None:
    await service.register("person@example.com", PASSWORD, "en", NOW)

    failures: list[ProductError] = []
    for email, password in (
        ("absent@example.com", PASSWORD),
        ("person@example.com", "this password is incorrect"),
    ):
        with pytest.raises(ProductError) as invalid:
            await service.login(email, password, NOW)
        failures.append(invalid.value)

    repository.deactivate("person@example.com")
    with pytest.raises(ProductError) as inactive:
        await service.login("person@example.com", PASSWORD, NOW)
    failures.append(inactive.value)

    assert {(error.code, error.status_code, error.message) for error in failures} == {
        ("AUTH_INVALID_CREDENTIALS", 401, "invalid credentials")
    }
    assert all("person@example.com" not in error.message for error in failures)


async def test_login_issues_access_and_refresh_tokens(
    service: AuthService,
    settings: Settings,
) -> None:
    registered = await service.register("person@example.com", PASSWORD, "en", NOW)

    issued = await service.login("person@example.com", PASSWORD, NOW)

    claims = decode_access_token(issued.access_token, settings)
    assert issued.user_id == registered.user_id
    assert issued.refresh_token
    assert claims["sub"] == str(issued.user_id)
    assert claims["session_id"]
    assert claims["token_version"] == 1


async def test_session_creation_rejection_uses_the_generic_credentials_error(
    service: AuthService,
    repository: InMemoryAuthRepository,
) -> None:
    email = "person@example.com"
    await service.register(email, PASSWORD, "en", NOW)
    repository.reject_session_creation = True

    with pytest.raises(ProductError) as rejected:
        await service.login(email, PASSWORD, NOW)

    assert (rejected.value.code, rejected.value.status_code, rejected.value.message) == (
        "AUTH_INVALID_CREDENTIALS",
        401,
        "invalid credentials",
    )
    assert email not in str(rejected.value)
    assert PASSWORD not in str(rejected.value)


async def test_refresh_rotates_a_valid_token(
    service: AuthService,
    settings: Settings,
) -> None:
    first = await service.register("person@example.com", PASSWORD, "en", NOW)

    second = await service.refresh(first.refresh_token, NOW)

    claims = decode_access_token(second.access_token, settings)
    assert second.user_id == first.user_id
    assert second.refresh_token != first.refresh_token
    assert claims["sub"] == str(first.user_id)


async def test_reusing_a_consumed_token_revokes_its_replacement(
    service: AuthService,
) -> None:
    await service.register("person@example.com", PASSWORD, "en", NOW)
    first = await service.login("person@example.com", PASSWORD, NOW)
    second = await service.refresh(first.refresh_token, NOW)

    with pytest.raises(ProductError, match="refresh token reuse detected") as reused:
        await service.refresh(first.refresh_token, NOW)

    assert reused.value.code == "AUTH_SESSION_REUSED"
    with pytest.raises(ProductError) as revoked:
        await service.refresh(second.refresh_token, NOW)
    assert revoked.value.code == "AUTH_INVALID_CREDENTIALS"


async def test_logout_is_idempotent_and_revokes_the_refresh_family(
    service: AuthService,
) -> None:
    issued = await service.register("person@example.com", PASSWORD, "ko", NOW)

    await service.logout(issued.refresh_token, NOW)
    await service.logout(issued.refresh_token, NOW)
    await service.logout(None, NOW)

    with pytest.raises(ProductError) as revoked:
        await service.refresh(issued.refresh_token, NOW)
    assert revoked.value.code == "AUTH_INVALID_CREDENTIALS"


@pytest.mark.parametrize("operation", ["register", "login"])
async def test_invalid_email_errors_do_not_disclose_the_submitted_email(
    service: AuthService,
    operation: str,
) -> None:
    submitted_email = "private-address-without-at-sign"

    with pytest.raises(ProductError) as invalid:
        if operation == "register":
            await service.register(submitted_email, PASSWORD, "en", NOW)
        else:
            await service.login(submitted_email, PASSWORD, NOW)

    assert (invalid.value.code, invalid.value.status_code, invalid.value.message) == (
        "VALIDATION_ERROR",
        422,
        "invalid authentication input",
    )
    assert submitted_email not in str(invalid.value)


@pytest.mark.parametrize("operation", ["register", "login"])
async def test_invalid_password_errors_do_not_disclose_the_submitted_password(
    service: AuthService,
    operation: str,
) -> None:
    submitted_password = "private-password-" + ("x" * 129)

    with pytest.raises(ProductError) as invalid:
        if operation == "register":
            await service.register("person@example.com", submitted_password, "en", NOW)
        else:
            await service.login("person@example.com", submitted_password, NOW)

    assert (invalid.value.code, invalid.value.status_code, invalid.value.message) == (
        "VALIDATION_ERROR",
        422,
        "invalid authentication input",
    )
    assert submitted_password not in str(invalid.value)


async def test_password_length_lower_boundary_rejects_11_and_accepts_12_characters(
    service: AuthService,
) -> None:
    too_short = "privatepass"

    with pytest.raises(ProductError) as invalid:
        await service.register("short@example.com", too_short, "en", NOW)

    assert (invalid.value.code, invalid.value.status_code, invalid.value.message) == (
        "VALIDATION_ERROR",
        422,
        "invalid authentication input",
    )
    assert too_short not in str(invalid.value)

    accepted = await service.register("exact@example.com", "x" * 12, "en", NOW)
    assert accepted.user_id


@pytest.mark.parametrize("operation", ["register", "login", "refresh", "logout"])
async def test_public_auth_operations_reject_naive_time(
    service: AuthService,
    repository: InMemoryAuthRepository,
    operation: str,
) -> None:
    issued = None
    if operation != "register":
        issued = await service.register("person@example.com", PASSWORD, "en", NOW)
    state_before = repository_state(repository)

    with pytest.raises(ValueError) as invalid:
        if operation == "register":
            await service.register("person@example.com", PASSWORD, "en", NOW.replace(tzinfo=None))
        elif operation == "login":
            await service.login("person@example.com", PASSWORD, NOW.replace(tzinfo=None))
        elif operation == "refresh":
            assert issued is not None
            await service.refresh(issued.refresh_token, NOW.replace(tzinfo=None))
        else:
            assert issued is not None
            await service.logout(issued.refresh_token, NOW.replace(tzinfo=None))

    assert str(invalid.value) == "authentication time must be timezone-aware"
    assert repository_state(repository) == state_before


async def test_public_auth_operations_normalize_aware_time_to_utc(
    service: AuthService,
    repository: InMemoryAuthRepository,
) -> None:
    offset_now = NOW.astimezone(timezone(timedelta(hours=9)))

    issued = await service.register("person@example.com", PASSWORD, "en", offset_now)
    await service.login("person@example.com", PASSWORD, offset_now)
    rotated = await service.refresh(issued.refresh_token, offset_now)
    await service.logout(rotated.refresh_token, offset_now)

    expected_expiry = NOW + timedelta(days=30)
    assert repository.last_session_expires_at == expected_expiry
    assert repository.last_session_expires_at is not None
    assert repository.last_session_expires_at.tzinfo is UTC
    assert repository.last_rotation_now == NOW
    assert repository.last_rotation_now is not None
    assert repository.last_rotation_now.tzinfo is UTC
    assert repository.last_rotation_expires_at == expected_expiry
    assert repository.last_rotation_expires_at is not None
    assert repository.last_rotation_expires_at.tzinfo is UTC
    assert repository.last_revocation_now == NOW
    assert repository.last_revocation_now is not None
    assert repository.last_revocation_now.tzinfo is UTC


async def test_registration_rejects_an_unsupported_locale_without_disclosing_it(
    service: AuthService,
) -> None:
    with pytest.raises(ProductError) as invalid:
        await service.register("person@example.com", PASSWORD, "private-locale", NOW)

    assert invalid.value.code == "VALIDATION_ERROR"
    assert "private-locale" not in str(invalid.value)


async def test_password_boundary_spaces_are_part_of_the_credential(service: AuthService) -> None:
    password_with_spaces = " leading and trailing spaces "
    await service.register("person@example.com", password_with_spaces, "en", NOW)

    await service.login("person@example.com", password_with_spaces, NOW)
    with pytest.raises(ProductError) as stripped:
        await service.login("person@example.com", password_with_spaces.strip(), NOW)

    assert stripped.value.code == "AUTH_INVALID_CREDENTIALS"
