# PANGAEA T-07 Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement email registration/login, 15-minute access JWTs, 30-day rotating refresh cookies, and token-family invalidation on reuse.

**Architecture:** A domain service orchestrates focused crypto and repository interfaces. PostgreSQL stores Argon2id credentials, session families, and hashed refresh-token lineage; Redis enforces the login sliding window. FastAPI owns validation, response envelopes, client-IP extraction, and HttpOnly cookie transport.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 async, PostgreSQL 16, Alembic, Redis 7, argon2-cffi, PyJWT, pytest, HTTPX.

## Global Constraints

- Base path is `/api/v1`; every response uses the existing success or error envelope.
- Email and password are the only implemented credentials; social providers remain behind `IdentityProvider`.
- Passwords use Argon2id. Access lifetime is exactly 900 seconds. Refresh lifetime defaults to exactly 30 days.
- Access product claims are only `sub`, `session_id`, and `token_version`; standard `iat` and `exp` claims are also required.
- Refresh values are never stored, logged, or returned in JSON. Only SHA-256 hashes are persisted.
- Refresh cookies are HttpOnly, SameSite=Lax, scoped to `/api/v1/auth`, and Secure in production.
- Reusing a consumed refresh token revokes its whole session family and returns `AUTH_SESSION_REUSED` 401.
- Login is limited to 10 attempts per source IP in a rolling 10-minute window; the eleventh returns `RATE_LIMITED` 429.
- Do not create profiles or acting-profile authorization in T-07; those belong to T-09 and T-08.
- Work test-first. A failing test must be observed before each production-code increment.

---

## File Map

- Modify `backend/pyproject.toml`: runtime crypto/JWT dependencies.
- Modify `.env.example`: documented local auth settings without production secrets.
- Modify `docker-compose.yml`: pass auth settings into the backend container.
- Modify `backend/app/settings.py`: token, cookie, and rate-limit settings.
- Create `backend/app/platform/crypto.py`: password hashing, refresh generation/hash, JWT issuing.
- Modify `backend/app/platform/db.py`: async session dependency used by auth routes.
- Modify `backend/app/platform/redis.py`: Redis dependency used by rate limiting.
- Create `backend/app/platform/rate_limit.py`: atomic sliding-window limiter.
- Modify `backend/app/domains/identity/models.py`: credential, session, and refresh models.
- Create `backend/app/domains/identity/providers.py`: social-provider port only.
- Create `backend/app/domains/identity/schemas.py`: domain records, results, and request/response models.
- Create `backend/app/domains/identity/repository.py`: PostgreSQL identity persistence and refresh locking.
- Create `backend/app/domains/identity/service.py`: auth use cases and safe error mapping.
- Create `backend/app/api/v1/auth.py`: four HTTP endpoints and refresh-cookie handling.
- Modify `backend/app/main.py`: register the auth router under `/api/v1`.
- Create `backend/migrations/versions/0002_auth_sessions.py`: auth schema migration.
- Modify `backend/tests/repository/test_initial_migration.py`: expected auth tables and columns.
- Create `backend/tests/unit/test_crypto.py`: primitive-level contracts.
- Create `backend/tests/unit/test_auth_service.py`: use-case contracts with a fake repository.
- Create `backend/tests/unit/test_rate_limit.py`: limiter threshold and expiry behavior.
- Create `backend/tests/integration/test_auth.py`: real PostgreSQL/Redis API flow and decisive reuse test.
- Create `backend/tests/integration/conftest.py`: isolated migrated database, Redis namespace, and app overrides.

### Task 1: Crypto primitives and settings

**Files:**

- Modify: `backend/pyproject.toml`
- Modify: `.env.example`
- Modify: `docker-compose.yml`
- Modify: `backend/app/settings.py`
- Create: `backend/app/platform/crypto.py`
- Test: `backend/tests/unit/test_crypto.py`

**Interfaces:**

- Produces: `PasswordService.hash(password: str) -> str`
- Produces: `PasswordService.verify(password_hash: str, password: str) -> bool`
- Produces: `new_refresh_token() -> str` and `hash_refresh_token(token: str) -> str`
- Produces: `issue_access_token(*, user_id: UUID, session_id: UUID, token_version: int, now: datetime, settings: Settings) -> str`

- [ ] **Step 1: Add failing primitive tests**

```python
def test_password_hash_is_argon2id_and_verifies_without_echoing_secret():
    encoded = PasswordService().hash("a-secure-password")
    assert encoded.startswith("$argon2id$")
    assert "a-secure-password" not in encoded
    assert PasswordService().verify(encoded, "a-secure-password") is True
    assert PasswordService().verify(encoded, "wrong-password") is False

def test_access_token_has_only_allowed_product_claims(settings):
    token = issue_access_token(user_id=USER_ID, session_id=SESSION_ID, token_version=2,
                               now=NOW, settings=settings)
    claims = jwt.decode(token, settings.jwt_signing_key.get_secret_value(), algorithms=["HS256"])
    assert set(claims) == {"sub", "session_id", "token_version", "iat", "exp"}
    assert claims["exp"] - claims["iat"] == 900
```

- [ ] **Step 2: Run the focused tests and observe RED**

Run: `docker compose run --rm backend python -m pytest tests/unit/test_crypto.py -q`

Expected: FAIL because `app.platform.crypto` does not exist.

- [ ] **Step 3: Add dependencies, exact settings, and minimal primitives**

Add `argon2-cffi>=25.1,<26`, `email-validator>=2.2,<3`, and `PyJWT>=2.10,<3`. Settings must expose `jwt_signing_key: SecretStr`, `rate_limit_pepper: SecretStr`, `access_token_ttl_seconds: int = 900`, `refresh_token_ttl_days: int = 30`, `refresh_cookie_name: str = "pangaea_refresh"`, and `refresh_cookie_secure: bool` derived from or validated against `app_env`. Document non-production local values in `.env.example` and pass all six environment variables through Compose. Production settings must reject the documented local signing key and must force secure cookies. Generate refresh tokens with `secrets.token_urlsafe(48)` and hash UTF-8 bytes with SHA-256.

```python
payload = {
    "sub": str(user_id),
    "session_id": str(session_id),
    "token_version": token_version,
    "iat": int(now.timestamp()),
    "exp": int((now + timedelta(seconds=settings.access_token_ttl_seconds)).timestamp()),
}
return jwt.encode(payload, settings.jwt_signing_key.get_secret_value(), algorithm="HS256")
```

- [ ] **Step 4: Rebuild and run the primitive tests GREEN**

Run: `docker compose build backend`

Run: `docker compose run --rm backend python -m pytest tests/unit/test_crypto.py -q`

Expected: all tests PASS.

- [ ] **Step 5: Commit the primitive slice**

```text
git add .env.example docker-compose.yml backend/pyproject.toml backend/app/settings.py backend/app/platform/crypto.py backend/tests/unit/test_crypto.py
git commit -m "feat(auth): add secure token primitives"
```

### Task 2: Auth persistence schema and migration

**Files:**

- Modify: `backend/app/domains/identity/models.py`
- Create: `backend/app/domains/identity/providers.py`
- Create: `backend/migrations/versions/0002_auth_sessions.py`
- Modify: `backend/tests/repository/test_initial_migration.py`

**Interfaces:**

- Produces: ORM models `PasswordCredential`, `AuthSession`, and `RefreshToken`.
- Produces: `IdentityProvider` protocol with `provider_name: str` and async `authenticate(assertion: str) -> ExternalIdentity`.
- Consumes: existing `User`, `Base`, `IdMixin`, `TimestampMixin`, and UUIDv7 defaults.

- [ ] **Step 1: Extend the migration test and observe RED**

Assert that `DOMAIN_TABLES` contains `password_credentials`, `auth_sessions`, and `refresh_tokens`; that `users.token_version` is non-null with default `1`; that no plaintext token column exists; and that `refresh_tokens.token_hash` is unique.

Run: `docker compose run --rm backend python -m pytest tests/repository/test_initial_migration.py -q`

Expected: FAIL because revision `0002` and the auth tables do not exist.

- [ ] **Step 2: Add the normalized auth models and migration**

Use these persistence fields:

```text
users.token_version INTEGER NOT NULL DEFAULT 1 CHECK > 0
password_credentials(user_id PK/FK, password_hash TEXT, created_at, updated_at)
auth_sessions(id PK, user_id FK, token_version, expires_at, revoked_at NULL,
              revocation_reason NULL, created_at, updated_at)
refresh_tokens(id PK, session_id FK, token_hash CHAR(64) UNIQUE, expires_at,
               consumed_at NULL, revoked_at NULL, replaced_by_token_id NULL FK,
               created_at)
```

Foreign-key deletes are `CASCADE` from user to credential/session and from session to refresh rows. The replacement self-reference uses `SET NULL`. Add indexes on `auth_sessions(user_id, revoked_at)` and `refresh_tokens(session_id, revoked_at)`. Downgrade removes indexes/tables, then `users.token_version`.

- [ ] **Step 3: Add the provider port without a social implementation**

```python
@dataclass(frozen=True)
class ExternalIdentity:
    provider: str
    subject: str
    email: str

class IdentityProvider(Protocol):
    provider_name: str
    async def authenticate(self, assertion: str) -> ExternalIdentity: ...
```

- [ ] **Step 4: Run migration upgrade/downgrade GREEN**

Run: `docker compose run --rm backend python -m pytest tests/repository/test_initial_migration.py -q`

Expected: PASS from an empty temporary PostgreSQL database.

- [ ] **Step 5: Commit the persistence slice**

```text
git add backend/app/domains/identity/models.py backend/app/domains/identity/providers.py backend/migrations/versions/0002_auth_sessions.py backend/tests/repository/test_initial_migration.py
git commit -m "feat(auth): persist refresh token families"
```

### Task 3: Repository and authentication service

**Files:**

- Modify: `backend/app/platform/db.py`
- Create: `backend/app/domains/identity/schemas.py`
- Create: `backend/app/domains/identity/repository.py`
- Create: `backend/app/domains/identity/service.py`
- Test: `backend/tests/unit/test_auth_service.py`

**Interfaces:**

- Produces: `AuthService.register(email: str, password: str, default_locale: str, now: datetime) -> IssuedAuth`
- Produces: `AuthService.login(email: str, password: str, now: datetime) -> IssuedAuth`
- Produces: `AuthService.refresh(refresh_token: str, now: datetime) -> IssuedAuth`
- Produces: `AuthService.logout(refresh_token: str | None, now: datetime) -> None`
- Produces: `IssuedAuth(user_id: UUID, access_token: str, refresh_token: str, expires_in: int)`
- Produces: `RotationStatus` values `ROTATED`, `REUSED`, and `INVALID`, returned with optional user/session identity.

- [ ] **Step 1: Write service tests with an in-memory fake and observe RED**

The tests must cover normalized registration, duplicate email 409, generic login 401 for absent/wrong/inactive users, successful session issue, valid rotation, consumed-token reuse, and idempotent logout. The decisive assertion is:

```python
first = await service.login("person@example.com", PASSWORD, NOW)
second = await service.refresh(first.refresh_token, NOW)
with pytest.raises(ProductError, match="refresh token reuse detected") as reused:
    await service.refresh(first.refresh_token, NOW)
assert reused.value.code == "AUTH_SESSION_REUSED"
with pytest.raises(ProductError) as revoked:
    await service.refresh(second.refresh_token, NOW)
assert revoked.value.code == "AUTH_INVALID_CREDENTIALS"
```

Run: `docker compose run --rm backend python -m pytest tests/unit/test_auth_service.py -q`

Expected: FAIL because the schemas, repository contract, and service do not exist.

- [ ] **Step 2: Implement records and the repository contract**

Define frozen records for login identity and rotation outcome. `SqlAlchemyAuthRepository` must own a transaction inside each mutating method so a `REUSED` result commits family revocation before the service raises. For rotation, select the refresh row with `with_for_update()`, reject unknown/expired/revoked/session-revoked/user-inactive tokens, and insert/link a replacement only for an unused token.

- [ ] **Step 3: Implement the service with fixed safe errors**

Validate email through Pydantic `EmailStr`, password length 12–128, and locale as `Literal["ko", "en"]`. Use one generic invalid-credentials message. On `REUSED`, raise only after the repository method returns from its committed transaction. Never put the submitted email or token in an error message.

- [ ] **Step 4: Run service tests and repository-focused tests GREEN**

Run: `docker compose run --rm backend python -m pytest tests/unit/test_auth_service.py tests/repository -q`

Expected: all tests PASS.

- [ ] **Step 5: Commit the domain slice**

```text
git add backend/app/platform/db.py backend/app/domains/identity/schemas.py backend/app/domains/identity/repository.py backend/app/domains/identity/service.py backend/tests/unit/test_auth_service.py
git commit -m "feat(auth): implement rotating session service"
```

### Task 4: Login limiter and HTTP API

**Files:**

- Modify: `backend/app/platform/redis.py`
- Create: `backend/app/platform/rate_limit.py`
- Create: `backend/app/api/v1/auth.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/unit/test_rate_limit.py`
- Create: `backend/tests/integration/conftest.py`
- Test: `backend/tests/integration/test_auth.py`

**Interfaces:**

- Produces: `SlidingWindowRateLimiter.check(key: str, *, limit: int, window_seconds: int, now_ms: int) -> RateLimitDecision`.
- Produces: POST `/api/v1/auth/register`, `/login`, `/refresh`, and `/logout`.
- Consumes: `AuthService`, `get_db_session`, Redis URL, and the existing envelope/error handlers.

- [ ] **Step 1: Write limiter and API contract tests and observe RED**

Use a unique rate-limit namespace per test. Test attempts 1–10 allowed, 11 denied with a positive retry delay, then allowance after the 600-second window. `conftest.py` must create a uniquely named PostgreSQL database, run Alembic through `head`, override the app database URL, use a unique Redis key prefix, and delete that database/prefix in `finally`. Integration tests must inspect `Set-Cookie` for `HttpOnly`, `SameSite=lax`, and `Path=/api/v1/auth`; ensure JSON contains no refresh token; and exercise the complete reuse sequence against real PostgreSQL and Redis.

Run: `docker compose run --rm backend python -m pytest tests/unit/test_rate_limit.py tests/integration/test_auth.py -q`

Expected: FAIL because the limiter and routes do not exist.

- [ ] **Step 2: Implement an atomic Redis sliding window**

Use a Lua script that removes scores `<= now_ms - window_ms`, counts the remaining members, inserts a unique request member only when below the limit, and sets key expiry to the window. Return `{allowed, retry_after_seconds}`. Hash the peer IP with a configured pepper before building the Redis key. Convert Redis connection errors to `DEPENDENCY_UNAVAILABLE` 503 without exposing connection details.

- [ ] **Step 3: Implement the four routes and cookie helper**

Register under `APIRouter(prefix="/api/v1/auth", tags=["auth"])`. Use status 201 for register and 200 for other success responses. `set_refresh_cookie` must set `httponly=True`, `secure=settings.refresh_cookie_secure`, `samesite="lax"`, `path="/api/v1/auth"`, and `max_age=refresh_token_ttl_days * 86400`. Logout always deletes the same cookie path. Determine login rate-limit identity from `request.client.host`; do not trust forwarded headers.

- [ ] **Step 4: Run focused and complete backend tests GREEN**

Run: `docker compose run --rm backend python -m pytest tests/unit/test_rate_limit.py tests/integration/test_auth.py -q`

Run: `docker compose run --rm backend python -m pytest -q -m "not live"`

Expected: all tests PASS.

- [ ] **Step 5: Commit the transport slice**

```text
git add backend/app/platform/redis.py backend/app/platform/rate_limit.py backend/app/api/v1/auth.py backend/app/main.py backend/tests/unit/test_rate_limit.py backend/tests/integration/conftest.py backend/tests/integration/test_auth.py
git commit -m "feat(auth): expose rate-limited auth API"
```

### Task 5: Full verification, review, and progress record

**Files:**

- Modify after implementation review: only files with confirmed defects.
- Modify after all checks: `docs/PROGRESS.md`

**Interfaces:**

- Consumes: all T-07 behavior and the repository-wide quality gates.
- Produces: reproducible T-07 completion evidence and the T-08 resume pointer.

- [ ] **Step 1: Run formatting and static checks**

Run: `docker compose run --rm backend ruff format --check .`

Run: `docker compose run --rm backend ruff check .`

Expected: both exit 0.

- [ ] **Step 2: Verify schema and live services from a clean application state**

Run: `docker compose up -d --wait postgres redis minio`

Run: `docker compose run --rm backend alembic upgrade head`

Run: `docker compose up -d --wait backend`

Run: `docker compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health/ready').read().decode())"`

Expected: Alembic reaches `0002`; readiness reports database, Redis, and migration as `ready`.

- [ ] **Step 3: Run repository-wide gates**

Run: `pnpm verify:pre-push`

Run: `pnpm --filter frontend exec playwright test`

Run: `docker compose config --quiet`

Expected: all commands exit 0; frontend regression tests remain green.

- [ ] **Step 4: Request a code review and fix only verified findings**

Review the committed T-07 range against `docs/SPEC.md`, the auth design, and the decisive reuse test. For any actionable defect, first add a failing regression test, then make the smallest fix and rerun focused plus full verification.

- [ ] **Step 5: Record progress in a separate commit**

Add a checked T-07 line with implementation commit hashes and exact test totals to `docs/PROGRESS.md`, then set the next resume point to T-08 `acting_profile_id` authorization context and IDOR guards.

```text
git add docs/PROGRESS.md
git commit -m "docs(progress): record t-07 completion"
```
