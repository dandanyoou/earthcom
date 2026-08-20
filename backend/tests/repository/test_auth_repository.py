import asyncio
from collections.abc import Awaitable
from datetime import UTC, datetime, timedelta
from time import monotonic

import pytest
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.identity.models import (
    AuthSession,
    PasswordCredential,
    RefreshToken,
    User,
)
from app.domains.identity.repository import DuplicateEmailError, SqlAlchemyAuthRepository
from app.domains.identity.schemas import RotationStatus
from app.domains.identity.service import AuthService
from app.errors import ProductError
from app.platform.crypto import PasswordService, hash_refresh_token
from app.settings import Settings
from tests.repository.conftest import RepositoryDatabase

NOW = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
FUTURE = NOW + timedelta(days=30)
PASSWORD = "correct horse battery staple"
TOKEN_1_HASH = hash_refresh_token("refresh-token-one")
TOKEN_2_HASH = hash_refresh_token("refresh-token-two")
TOKEN_3_HASH = hash_refresh_token("refresh-token-three")
UNKNOWN_TOKEN_HASH = hash_refresh_token("unknown-refresh-token")


async def seed_family(
    database: RepositoryDatabase,
    *,
    token_hash: str = TOKEN_1_HASH,
) -> tuple[SqlAlchemyAuthRepository, AsyncSession, User, AuthSession]:
    session = database.sessions()
    repository = SqlAlchemyAuthRepository(session)
    identity = await repository.create_identity(
        email="person@example.com",
        password_hash="stored-password-hash",
        default_locale="en",
    )
    issued_session = await repository.create_session(
        user_id=identity.user_id,
        token_version=identity.token_version,
        refresh_token_hash=token_hash,
        expires_at=FUTURE,
    )
    async with database.sessions() as inspection:
        user = await inspection.get(User, identity.user_id)
        auth_session = await inspection.get(AuthSession, issued_session.session_id)
        assert user is not None
        assert auth_session is not None
        inspection.expunge(user)
        inspection.expunge(auth_session)
    return repository, session, user, auth_session


async def test_valid_rotation_consumes_and_links_the_stored_replacement(
    repository_database: RepositoryDatabase,
) -> None:
    repository, repository_session, _, auth_session = await seed_family(repository_database)
    try:
        outcome = await repository.rotate_refresh(
            refresh_token_hash=TOKEN_1_HASH,
            replacement_token_hash=TOKEN_2_HASH,
            replacement_expires_at=FUTURE + timedelta(days=1),
            now=NOW,
        )

        async with repository_database.sessions() as inspection:
            tokens = list(
                (
                    await inspection.scalars(
                        select(RefreshToken)
                        .where(RefreshToken.session_id == auth_session.id)
                        .order_by(RefreshToken.created_at, RefreshToken.id)
                    )
                ).all()
            )

        assert outcome.status is RotationStatus.ROTATED
        assert len(tokens) == 2
        original = next(token for token in tokens if token.token_hash == TOKEN_1_HASH)
        replacement = next(token for token in tokens if token.token_hash == TOKEN_2_HASH)
        assert original.consumed_at == NOW
        assert original.replaced_by_token_id == replacement.id
        assert replacement.expires_at == FUTURE
        assert replacement.consumed_at is None
        assert replacement.revoked_at is None
    finally:
        await repository_session.close()


@pytest.mark.parametrize(
    "invalid_state",
    [
        "unknown_token",
        "expired_token",
        "revoked_token",
        "expired_session",
        "revoked_session",
        "inactive_user",
        "token_version_mismatch",
    ],
)
async def test_rotation_rejects_every_invalid_family_state_without_inserting_a_replacement(
    repository_database: RepositoryDatabase,
    invalid_state: str,
) -> None:
    repository, repository_session, user, auth_session = await seed_family(repository_database)
    submitted_hash = TOKEN_1_HASH
    try:
        if invalid_state == "unknown_token":
            submitted_hash = UNKNOWN_TOKEN_HASH
        else:
            async with repository_database.sessions.begin() as mutation:
                if invalid_state == "expired_token":
                    await mutation.execute(
                        update(RefreshToken)
                        .where(RefreshToken.token_hash == TOKEN_1_HASH)
                        .values(expires_at=NOW)
                    )
                elif invalid_state == "revoked_token":
                    await mutation.execute(
                        update(RefreshToken)
                        .where(RefreshToken.token_hash == TOKEN_1_HASH)
                        .values(revoked_at=NOW)
                    )
                elif invalid_state == "expired_session":
                    await mutation.execute(
                        update(AuthSession)
                        .where(AuthSession.id == auth_session.id)
                        .values(expires_at=NOW)
                    )
                elif invalid_state == "revoked_session":
                    await mutation.execute(
                        update(AuthSession)
                        .where(AuthSession.id == auth_session.id)
                        .values(revoked_at=NOW)
                    )
                elif invalid_state == "inactive_user":
                    await mutation.execute(
                        update(User).where(User.id == user.id).values(status="SUSPENDED")
                    )
                elif invalid_state == "token_version_mismatch":
                    await mutation.execute(
                        update(User).where(User.id == user.id).values(token_version=2)
                    )

        outcome = await repository.rotate_refresh(
            refresh_token_hash=submitted_hash,
            replacement_token_hash=TOKEN_2_HASH,
            replacement_expires_at=FUTURE,
            now=NOW,
        )

        async with repository_database.sessions() as inspection:
            replacement_count = await inspection.scalar(
                select(func.count())
                .select_from(RefreshToken)
                .where(RefreshToken.token_hash == TOKEN_2_HASH)
            )
            original = await inspection.scalar(
                select(RefreshToken).where(RefreshToken.token_hash == TOKEN_1_HASH)
            )

        assert outcome.status is RotationStatus.INVALID
        assert replacement_count == 0
        assert original is not None
        assert original.consumed_at is None
    finally:
        await repository_session.close()


async def test_reuse_revocation_is_committed_before_the_service_raises(
    repository_database: RepositoryDatabase,
) -> None:
    async with repository_database.sessions() as session:
        service = AuthService(
            repository=SqlAlchemyAuthRepository(session),
            password_service=PasswordService(),
            settings=Settings(
                jwt_signing_key="test-signing-key-with-at-least-32b",
                rate_limit_pepper="test-rate-limit-pepper",
            ),
        )
        first = await service.register("person@example.com", PASSWORD, "en", NOW)
        second = await service.refresh(first.refresh_token, NOW)

        with pytest.raises(ProductError) as reused:
            await service.refresh(first.refresh_token, NOW)

        assert reused.value.code == "AUTH_SESSION_REUSED"
        with pytest.raises(ProductError) as invalid:
            await service.refresh(second.refresh_token, NOW)
        assert invalid.value.code == "AUTH_INVALID_CREDENTIALS"

    async with repository_database.sessions() as inspection:
        auth_session = await inspection.scalar(select(AuthSession))
        tokens = list((await inspection.scalars(select(RefreshToken))).all())

    assert auth_session is not None
    assert auth_session.revoked_at == NOW
    assert auth_session.revocation_reason == "REFRESH_TOKEN_REUSE"
    assert len(tokens) == 2
    assert all(token.revoked_at == NOW for token in tokens)


async def test_duplicate_rollback_leaves_the_sqlalchemy_session_usable(
    repository_database: RepositoryDatabase,
) -> None:
    async with repository_database.sessions() as session:
        repository = SqlAlchemyAuthRepository(session)
        identity = await repository.create_identity(
            email="person@example.com",
            password_hash="stored-password-hash",
            default_locale="en",
        )

        with pytest.raises(DuplicateEmailError):
            await repository.create_identity(
                email="person@example.com",
                password_hash="different-password-hash",
                default_locale="ko",
            )

        issued_session = await repository.create_session(
            user_id=identity.user_id,
            token_version=identity.token_version,
            refresh_token_hash=TOKEN_1_HASH,
            expires_at=FUTURE,
        )
        found = await repository.find_login_identity("person@example.com")

    async with repository_database.sessions() as inspection:
        credential_count = await inspection.scalar(
            select(func.count()).select_from(PasswordCredential)
        )
        session_count = await inspection.scalar(select(func.count()).select_from(AuthSession))

    assert found == identity
    assert issued_session.user_id == identity.user_id
    assert credential_count == 1
    assert session_count == 1


async def test_logout_revokes_the_whole_family_and_is_idempotent(
    repository_database: RepositoryDatabase,
) -> None:
    repository, repository_session, _, auth_session = await seed_family(repository_database)
    try:
        await repository.rotate_refresh(
            refresh_token_hash=TOKEN_1_HASH,
            replacement_token_hash=TOKEN_2_HASH,
            replacement_expires_at=FUTURE,
            now=NOW,
        )

        await repository.revoke_refresh_family(refresh_token_hash=TOKEN_2_HASH, now=NOW)
        await repository.revoke_refresh_family(refresh_token_hash=TOKEN_2_HASH, now=NOW)
        await repository.revoke_refresh_family(refresh_token_hash=UNKNOWN_TOKEN_HASH, now=NOW)

        async with repository_database.sessions() as inspection:
            stored_session = await inspection.get(AuthSession, auth_session.id)
            tokens = list((await inspection.scalars(select(RefreshToken))).all())

        assert stored_session is not None
        assert stored_session.revoked_at == NOW
        assert stored_session.revocation_reason == "LOGOUT"
        assert len(tokens) == 2
        assert all(token.revoked_at == NOW for token in tokens)
    finally:
        await repository_session.close()


async def wait_for_database_waiters(
    database: RepositoryDatabase,
    *,
    minimum: int,
) -> None:
    deadline = monotonic() + 5
    while monotonic() < deadline:
        async with database.engine.connect() as observer:
            waiters = await observer.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND wait_event_type = 'Lock'"
                )
            )
        if waiters is not None and waiters >= minimum:
            return
        await asyncio.sleep(0.02)
    raise AssertionError(f"expected at least {minimum} blocked database operations")


async def await_outcome(task: Awaitable[object]) -> object:
    return await asyncio.wait_for(task, timeout=5)


async def wait_until_done_or_database_waiter(
    database: RepositoryDatabase,
    task: asyncio.Task[object],
) -> None:
    deadline = monotonic() + 5
    while monotonic() < deadline:
        if task.done():
            return
        async with database.engine.connect() as observer:
            waiters = await observer.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND wait_event_type = 'Lock'"
                )
            )
        if waiters is not None and waiters >= 1:
            return
        await asyncio.sleep(0.02)
    raise AssertionError("repository operation neither completed nor waited for the user lock")


async def apply_user_security_change(
    connection: object,
    *,
    user_id: object,
    security_change: str,
) -> None:
    if security_change == "suspension":
        statement = "UPDATE users SET status = 'SUSPENDED' WHERE id = :user_id"
    else:
        statement = "UPDATE users SET token_version = token_version + 1 WHERE id = :user_id"
    await connection.execute(text(statement), {"user_id": user_id})


@pytest.mark.parametrize("security_change", ["suspension", "token_version_increment"])
async def test_session_creation_loses_to_a_committed_user_security_change(
    repository_database: RepositoryDatabase,
    security_change: str,
) -> None:
    async with repository_database.sessions() as setup_session:
        identity = await SqlAlchemyAuthRepository(setup_session).create_identity(
            email="person@example.com",
            password_hash="stored-password-hash",
            default_locale="en",
        )

    async with (
        repository_database.engine.connect() as mutator,
        repository_database.sessions() as contender_session,
    ):
        transaction = await mutator.begin()
        await apply_user_security_change(
            mutator,
            user_id=identity.user_id,
            security_change=security_change,
        )
        contender = asyncio.create_task(
            SqlAlchemyAuthRepository(contender_session).create_session(
                user_id=identity.user_id,
                token_version=identity.token_version,
                refresh_token_hash=TOKEN_1_HASH,
                expires_at=FUTURE,
            )
        )
        await wait_until_done_or_database_waiter(repository_database, contender)
        await transaction.commit()
        created = await await_outcome(contender)

    async with repository_database.sessions() as inspection:
        session_count = await inspection.scalar(select(func.count()).select_from(AuthSession))
        token_count = await inspection.scalar(select(func.count()).select_from(RefreshToken))

    assert created is None
    assert session_count == 0
    assert token_count == 0


async def test_session_creation_refreshes_cached_user_state_under_lock(
    repository_database: RepositoryDatabase,
) -> None:
    async with repository_database.sessions() as repository_session:
        repository = SqlAlchemyAuthRepository(repository_session)
        identity = await repository.create_identity(
            email="person@example.com",
            password_hash="stored-password-hash",
            default_locale="en",
        )
        cached_user = await repository_session.get(User, identity.user_id)
        await repository_session.commit()
        assert cached_user is not None
        assert cached_user.status == "ACTIVE"

        async with repository_database.engine.begin() as mutator:
            await mutator.execute(
                text("UPDATE users SET status = 'SUSPENDED' WHERE id = :user_id"),
                {"user_id": identity.user_id},
            )

        created = await repository.create_session(
            user_id=identity.user_id,
            token_version=identity.token_version,
            refresh_token_hash=TOKEN_1_HASH,
            expires_at=FUTURE,
        )

    async with repository_database.sessions() as inspection:
        session_count = await inspection.scalar(select(func.count()).select_from(AuthSession))

    assert created is None
    assert session_count == 0


@pytest.mark.parametrize("security_change", ["suspension", "token_version_increment"])
async def test_refresh_loses_to_a_committed_user_security_change(
    repository_database: RepositoryDatabase,
    security_change: str,
) -> None:
    _, setup_session, user, auth_session = await seed_family(repository_database)
    await setup_session.close()

    async with (
        repository_database.engine.connect() as mutator,
        repository_database.sessions() as contender_session,
    ):
        transaction = await mutator.begin()
        await apply_user_security_change(
            mutator,
            user_id=user.id,
            security_change=security_change,
        )
        contender = asyncio.create_task(
            SqlAlchemyAuthRepository(contender_session).rotate_refresh(
                refresh_token_hash=TOKEN_1_HASH,
                replacement_token_hash=TOKEN_2_HASH,
                replacement_expires_at=FUTURE,
                now=NOW,
            )
        )
        await wait_until_done_or_database_waiter(repository_database, contender)
        await mutator.execute(
            text("SELECT id FROM auth_sessions WHERE id = :session_id FOR UPDATE NOWAIT"),
            {"session_id": auth_session.id},
        )
        await mutator.execute(
            text("SELECT id FROM refresh_tokens WHERE token_hash = :token_hash FOR UPDATE NOWAIT"),
            {"token_hash": TOKEN_1_HASH},
        )
        await transaction.commit()
        outcome = await await_outcome(contender)

    async with repository_database.sessions() as inspection:
        original = await inspection.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == TOKEN_1_HASH)
        )
        replacement_count = await inspection.scalar(
            select(func.count())
            .select_from(RefreshToken)
            .where(RefreshToken.token_hash == TOKEN_2_HASH)
        )

    assert outcome.status is RotationStatus.INVALID
    assert original is not None
    assert original.consumed_at is None
    assert replacement_count == 0


async def test_concurrent_reuse_and_rotation_revoke_every_family_row(
    repository_database: RepositoryDatabase,
) -> None:
    setup_repository, setup_session, _, auth_session = await seed_family(repository_database)
    await setup_repository.rotate_refresh(
        refresh_token_hash=TOKEN_1_HASH,
        replacement_token_hash=TOKEN_2_HASH,
        replacement_expires_at=FUTURE,
        now=NOW,
    )
    await setup_session.close()

    advisory_key = 741_903_127
    async with repository_database.engine.begin() as connection:
        await connection.execute(
            text(
                "CREATE FUNCTION block_test_replacement() RETURNS trigger AS $$ "
                "BEGIN "
                f"IF NEW.token_hash = '{TOKEN_3_HASH}' THEN "
                f"PERFORM pg_advisory_xact_lock({advisory_key}); "
                "END IF; "
                "RETURN NEW; "
                "END; $$ LANGUAGE plpgsql"
            )
        )
        await connection.execute(
            text(
                "CREATE TRIGGER block_test_replacement_trigger "
                "BEFORE INSERT ON refresh_tokens "
                "FOR EACH ROW EXECUTE FUNCTION block_test_replacement()"
            )
        )

    async with (
        repository_database.engine.connect() as controller,
        repository_database.sessions() as rotating_session,
        repository_database.sessions() as reusing_session,
    ):
        await controller.execute(text("SELECT pg_advisory_lock(:key)"), {"key": advisory_key})
        rotating_repository = SqlAlchemyAuthRepository(rotating_session)
        reusing_repository = SqlAlchemyAuthRepository(reusing_session)

        rotation_task = asyncio.create_task(
            rotating_repository.rotate_refresh(
                refresh_token_hash=TOKEN_2_HASH,
                replacement_token_hash=TOKEN_3_HASH,
                replacement_expires_at=FUTURE,
                now=NOW,
            )
        )
        await wait_for_database_waiters(repository_database, minimum=1)

        reuse_task = asyncio.create_task(
            reusing_repository.rotate_refresh(
                refresh_token_hash=TOKEN_1_HASH,
                replacement_token_hash=UNKNOWN_TOKEN_HASH,
                replacement_expires_at=FUTURE,
                now=NOW,
            )
        )
        await wait_for_database_waiters(repository_database, minimum=2)
        await controller.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": advisory_key})

        rotated, reused = await asyncio.gather(
            await_outcome(rotation_task),
            await_outcome(reuse_task),
        )

    async with repository_database.sessions() as inspection:
        stored_session = await inspection.get(AuthSession, auth_session.id)
        tokens = list((await inspection.scalars(select(RefreshToken))).all())

    assert rotated.status is RotationStatus.ROTATED
    assert reused.status is RotationStatus.REUSED
    assert stored_session is not None
    assert stored_session.revoked_at == NOW
    assert len(tokens) == 3
    assert all(token.revoked_at == NOW for token in tokens)
