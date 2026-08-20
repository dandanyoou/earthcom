# PANGAEA P0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the reproducible, tested PANGAEA monorepo foundation for T-01 through T-06, followed by T-47 and T-48, so later product phases can add behavior without changing the toolchain, runtime contracts, design tokens, locale routing, or responsive shell.

**Architecture:** Use one pnpm workspace for root tooling and the Next.js frontend, plus a Python 3.12 FastAPI package run through Docker Compose. PostgreSQL, Redis, and MinIO are the only stateful services. Page content remains independent of viewport; an `AppShell` selects mobile or desktop navigation with CSS while the same components render in both.

**Tech Stack:** pnpm 11, Node.js 22/24, Next.js 15, React 19, TypeScript 5, Tailwind CSS 4, next-intl, Vitest, Playwright, Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL 16 with pgvector, Redis 7, MinIO, Ruff, Pytest, Husky, commitlint, Prettier, ESLint.

## Global Constraints

- Treat `docs/SPEC.md` and `docs/reference/PANGAEA_데모_수정.html` as the repository-local source of truth.
- Implement P0 in this order: T-01, T-02, T-03, T-04, T-05, T-06, T-47, T-48.
- Use Next.js 15 App Router, TypeScript, Tailwind CSS v4, and `next-intl`.
- Use FastAPI on Python 3.12, SQLAlchemy 2.x, Pydantic v2, and Alembic.
- Use PostgreSQL 16 with pgvector, Redis 7, and MinIO through Docker Compose.
- Keep `AI_MODE=stub`, `DEPOSIT_PROVIDER=sandbox`, `DEPOSIT_PRODUCTION_ENABLED=false`, and `DEPOSIT_FORFEITURE_ENABLED=false` as defaults.
- Never place `OPENAI_API_KEY` or a direct OpenAI URL in frontend source, configuration, or bundles.
- Keep all directories lowercase and use Conventional Commits.
- Never bypass Husky with `--no-verify`.
- Keep UI strings in `frontend/messages/ko.json` and `frontend/messages/en.json`; JSX Korean literals must fail lint.
- Keep page components viewport-agnostic; only shell components may contain responsive layout rules.
- Preserve the exact color tokens and component contracts from specification §4.
- Use inline monochrome SVG icons; do not use flag emoji, decorative gradients, Inter, or multi-column card grids.
- Before every task commit, run `git add -A` and inspect `git -c core.quotepath=false diff --cached --stat`.
- After each implementation commit, add a `docs(PROGRESS)` commit that records the implementation commit hash and test result. This two-commit protocol avoids an impossible self-referential commit hash while still leaving every completed task resumable.
- Work on `feature/T-01-foundation`; do not commit to `main`.

## File and Responsibility Map

```text
.
├─ .github/workflows/ci.yml             # P0 lint, type, backend, migration, and UI checks
├─ .husky/{pre-commit,commit-msg,pre-push}
├─ docs/{SPEC.md,PROGRESS.md,DECISIONS.md}
├─ docs/reference/PANGAEA_데모_수정.html
├─ scripts/
│  ├─ check_i18n_parity.mjs             # locale key equality
│  ├─ check_page_responsive_boundary.mjs # responsive-code ownership
│  └─ verify_git_hooks.mjs               # actual hook probes
├─ frontend/
│  ├─ app/[locale]/...                   # locale routes and shell entry
│  ├─ components/shell/...               # responsive navigation containers
│  ├─ components/ui/...                  # demo-derived primitives
│  ├─ messages/{ko,en}.json              # all user-visible copy
│  ├─ styles/tokens.css                  # immutable §4.2 variables
│  └─ e2e/p0-shell.spec.ts               # visual and navigation checks
├─ backend/
│  ├─ app/api/v1/health.py               # liveness and readiness
│  ├─ app/platform/{db,redis}.py          # dependency checks
│  ├─ app/{main,settings,envelope,errors}.py
│  ├─ migrations/versions/...            # P0 identity/profile schema
│  └─ tests/...                           # unit, migration, integration contracts
├─ docker-compose.yml
├─ package.json
└─ pnpm-workspace.yaml
```

## Task 1: T-01 Repository Workspace and Enforced Git Hooks

**Files:**

- Create: `.editorconfig`
- Create: `.gitattributes`
- Create: `.gitignore`
- Create: `.npmrc`
- Create: `.prettierignore`
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `prettier.config.mjs`
- Create: `eslint.config.mjs`
- Create: `commitlint.config.mjs`
- Create: `.husky/pre-commit`
- Create: `.husky/commit-msg`
- Create: `.husky/pre-push`
- Create: `scripts/verify_git_hooks.mjs`
- Create: `scripts/tests/toolchain_behavior.test.mjs`
- Create: `docs/SPEC.md`
- Create: `docs/reference/PANGAEA_데모_수정.html`
- Create: `docs/PROGRESS.md`
- Create: `docs/DECISIONS.md`
- Modify: `README.md`
- Test: `scripts/tests/toolchain_behavior.test.mjs`

**Interfaces:**

- Consumes: the two user-supplied source files and Git branch `feature/T-01-foundation`.
- Produces: root commands `format:check`, `lint`, `typecheck`, `test`, `check:hooks`, and `verify:pre-push`; protected Git hooks; repository-local specification and progress records.

- [ ] **Step 1: Write the failing toolchain behavior test**

```js
// scripts/tests/toolchain_behavior.test.mjs
import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const pnpm = process.platform === "win32" ? "pnpm.cmd" : "pnpm";
const run = (args) => spawnSync(pnpm, args, { encoding: "utf8" });

test("formatter rejects unformatted markdown and accepts its own output", async () => {
  const directory = await mkdtemp(join(tmpdir(), "pangaea-format-"));
  const file = join(directory, "probe.md");
  try {
    await writeFile(file, "# heading\n\n-   badly spaced\n", "utf8");
    assert.notEqual(run(["exec", "prettier", "--check", file]).status, 0);
    assert.equal(run(["exec", "prettier", "--write", file]).status, 0);
    assert.equal(run(["exec", "prettier", "--check", file]).status, 0);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("linter rejects an explicit-any API-key literal", async () => {
  const file = ".toolchain-probe.ts";
  try {
    await writeFile(file, 'const secret: any = "sk-probe";\n', "utf8");
    const result = run(["exec", "eslint", file, "--max-warnings=0"]);
    assert.notEqual(result.status, 0, `${result.stdout}\n${result.stderr}`);
  } finally {
    await rm(file, { force: true });
  }
});
```

- [ ] **Step 2: Run the contract and confirm the missing-foundation failure**

Run: `node --test scripts/tests/toolchain_behavior.test.mjs`

Expected: FAIL because `package.json`, hooks, and repository-local source documents do not exist.

- [ ] **Step 3: Add the root workspace and formatting configuration**

```json
// package.json
{
  "name": "pangaea",
  "private": true,
  "packageManager": "pnpm@11.19.0",
  "engines": { "node": ">=22 <25" },
  "scripts": {
    "prepare": "husky",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "lint": "eslint . --max-warnings=0",
    "typecheck": "pnpm -r --if-present typecheck",
    "test": "node --test scripts/tests/*.test.mjs && pnpm -r --if-present test",
    "check:hooks": "node scripts/verify_git_hooks.mjs",
    "verify:pre-push": "pnpm format:check && pnpm lint && pnpm typecheck && pnpm test"
  },
  "lint-staged": {
    "*.{ts,tsx,js,jsx,mjs}": ["prettier --write", "eslint --fix --max-warnings=0"],
    "*.{json,md,css,yml,yaml}": ["prettier --write"],
    "*.py": ["ruff check --fix", "ruff format"]
  },
  "devDependencies": {
    "@commitlint/cli": "^19.8.1",
    "@commitlint/config-conventional": "^19.8.1",
    "@eslint/js": "^9.33.0",
    "@typescript-eslint/eslint-plugin": "^8.39.1",
    "@typescript-eslint/parser": "^8.39.1",
    "eslint": "^9.33.0",
    "globals": "^16.3.0",
    "husky": "^9.1.7",
    "lint-staged": "^16.1.5",
    "prettier": "^3.6.2",
    "prettier-plugin-tailwindcss": "^0.6.14",
    "typescript-eslint": "^8.39.1"
  }
}
```

```yaml
# pnpm-workspace.yaml
packages:
  - frontend
```

Set `.npmrc` to `engine-strict=true`, normalize text to LF in `.gitattributes`, ignore dependency/build/cache/env artifacts in `.gitignore`, and configure Prettier with `printWidth: 100`, `semi: true`, `singleQuote: false`, and `plugins: ["prettier-plugin-tailwindcss"]`. Add `docs/SPEC.md` and `docs/reference/` to `.prettierignore` so source-of-truth artifacts remain byte-stable.

- [ ] **Step 4: Add enforced ESLint and commitlint rules**

```js
// eslint.config.mjs
import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default [
  { ignores: ["**/node_modules/**", "**/.next/**", "**/playwright-report/**"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "no-restricted-imports": ["error", { patterns: ["openai", "@anthropic-ai/*"] }],
      "no-restricted-syntax": [
        "error",
        { selector: "Literal[value=/^sk-/]", message: "API 키를 프론트에 두지 않는다" },
        {
          selector: "JSXText[value=/[가-힣]/]",
          message: "화면 문구는 messages/*.json에서 가져온다 (§4.8)",
        },
      ],
    },
  },
];
```

```js
// commitlint.config.mjs
export default { extends: ["@commitlint/config-conventional"] };
```

- [ ] **Step 5: Add hooks and an executable hook probe**

```sh
# .husky/pre-commit
pnpm exec lint-staged
```

```sh
# .husky/commit-msg
pnpm exec commitlint --edit "$1"
```

```sh
# .husky/pre-push
pnpm verify:pre-push
```

`scripts/verify_git_hooks.mjs` must perform three real subprocess checks and always clean up in `finally`:

1. Write and stage `.hook-probe.ts` containing `const secret: any = "sk-hook-probe";`, run `.husky/pre-commit`, and assert a non-zero exit.
2. Write an invalid commit message to the OS temporary directory, run `.husky/commit-msg <file>`, and assert a non-zero exit.
3. Run `.husky/pre-push` against the clean workspace and assert exit zero.

- [ ] **Step 6: Add repository-local source documents and handoff files**

Copy the UTF-8 contents of `C:\Users\User\Downloads\PANGAEA_통합_개발명세서_v1.0.md` verbatim to `docs/SPEC.md` and `C:\Users\User\Downloads\PANGAEA_데모_수정.html` verbatim to `docs/reference/PANGAEA_데모_수정.html`. Initialize `docs/PROGRESS.md` with unchecked T-01 through T-50 rows and the exact progress-line format from specification §13. Initialize `docs/DECISIONS.md` with the two-commit progress protocol and the reason self-referential hashes cannot be stored in the same Git commit.

- [ ] **Step 7: Install dependencies and verify all hooks**

Run: `pnpm install`  
Run: `node --test scripts/tests/toolchain_behavior.test.mjs`

Run: `pnpm check:hooks`  
Expected: workspace contract PASS; pre-commit and commit-msg probes are rejected; pre-push probe passes.

- [ ] **Step 8: Commit T-01 and record progress**

```powershell
git add -A
git -c core.quotepath=false diff --cached --stat
git commit -m "chore(repo): T-01 initialize workspace and enforced hooks"
$implementationCommit = git rev-parse --short HEAD
```

Add `- [x] T-01 레포 초기화와 훅 — 2026-08-13 · 커밋 $implementationCommit · workspace contract와 hook probe 통과` to `docs/PROGRESS.md`, then commit it as `docs(progress): record T-01 completion`.

## Task 2: T-02 PostgreSQL, Redis, and MinIO Compose Stack

**Files:**

- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `scripts/test_infra.mjs`
- Create: `scripts/tests/compose_contract.test.mjs`
- Modify: `package.json`
- Modify: `docs/PROGRESS.md`
- Test: `scripts/tests/compose_contract.test.mjs`

**Interfaces:**

- Consumes: root pnpm scripts and Docker Compose.
- Produces: services `postgres:5432`, `redis:6379`, `minio:9000/9001`; volume names scoped by the Compose project; health checks; root commands `infra:up`, `infra:down`, and `test:infra`.

- [ ] **Step 1: Write the failing Compose contract**

```js
// scripts/tests/compose_contract.test.mjs
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import test from "node:test";

const config = () => execFileSync("docker", ["compose", "config"], { encoding: "utf8" });

test("compose defines healthy stateful dependencies", () => {
  const yaml = config();
  for (const service of ["postgres:", "redis:", "minio:"]) assert.match(yaml, new RegExp(service));
  assert.match(yaml, /pgvector\/pgvector:pg16/);
  assert.match(yaml, /redis:7/);
  assert.match(yaml, /healthcheck:/);
});
```

- [ ] **Step 2: Run the contract and confirm failure**

Run: `node --test scripts/tests/compose_contract.test.mjs`  
Expected: FAIL because `docker-compose.yml` is absent.

- [ ] **Step 3: Add pinned services and safe local defaults**

Use `pgvector/pgvector:pg16`, `redis:7-alpine`, and `minio/minio:RELEASE.2025-04-22T22-12-26Z`. Configure PostgreSQL database/user/password as `pangaea`, Redis persistence with append-only mode, MinIO bucket credentials from `.env`, named volumes, and health checks using `pg_isready`, `redis-cli ping`, and MinIO `/minio/health/live`. Do not expose credentials other than documented local development values in `.env.example`.

- [ ] **Step 4: Add executable infrastructure verification**

Add a cross-platform `scripts/test_infra.mjs` that uses `execFileSync("docker", args)` for `compose up -d --wait`, PostgreSQL extension creation/query, Redis `PING`, and MinIO health status. Add root scripts:

```json
{
  "infra:up": "docker compose up -d postgres redis minio",
  "infra:down": "docker compose down",
  "test:infra": "node scripts/test_infra.mjs"
}
```

- [ ] **Step 5: Run configuration and live-service tests**

Run: `docker compose config --quiet`  
Run: `pnpm test:infra`  
Expected: Compose config succeeds, all three services become healthy, vector extension query returns `vector`, and Redis returns `PONG`.

- [ ] **Step 6: Commit T-02 and record progress**

Commit implementation as `chore(infra): T-02 add local stateful services`, then record the short hash and verification commands in `docs/PROGRESS.md` and commit as `docs(progress): record T-02 completion`.

## Task 3: T-03 FastAPI Skeleton, Envelopes, Errors, and Health

**Files:**

- Create: `backend/pyproject.toml`
- Create: `backend/Dockerfile`
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/script.py.mako`
- Create: `backend/migrations/versions/.gitkeep`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/settings.py`
- Create: `backend/app/envelope.py`
- Create: `backend/app/errors.py`
- Create: `backend/app/api/v1/health.py`
- Create: `backend/app/platform/db.py`
- Create: `backend/app/platform/redis.py`
- Create: `scripts/ruff_staged.mjs`
- Create: `backend/tests/unit/test_envelope.py`
- Create: `backend/tests/integration/test_health.py`
- Modify: `docker-compose.yml`
- Modify: `package.json`
- Modify: `.husky/pre-push`
- Modify: `docs/PROGRESS.md`

**Interfaces:**

- Consumes: `DATABASE_URL`, `REDIS_URL`, and Compose health dependencies.
- Produces: `create_app() -> FastAPI`; `ok(data, meta=None) -> SuccessEnvelope`; `ProductError(code, message, status_code, details)`; `GET /health/live`; `GET /health/ready`.

- [ ] **Step 1: Write failing envelope and health tests**

```python
# backend/tests/unit/test_envelope.py
from app.envelope import ok

def test_success_envelope_has_one_data_layer() -> None:
    assert ok({"value": 1}).model_dump() == {
        "ok": True,
        "data": {"value": 1},
        "meta": None,
    }
```

```python
# backend/tests/integration/test_health.py
from fastapi.testclient import TestClient
from app.main import create_app

def test_live_does_not_depend_on_infrastructure() -> None:
    response = TestClient(create_app()).get("/health/live")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "live"
```

- [ ] **Step 2: Run tests and confirm import failures**

Run: `docker compose run --rm backend python -m pytest tests/unit/test_envelope.py tests/integration/test_health.py -q`  
Expected: FAIL because the backend package and Compose service do not exist.

- [ ] **Step 3: Add the Python 3.12 package and settings**

Set `requires-python = ">=3.12,<3.13"`. Add runtime dependencies for FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy async, psycopg 3, Redis asyncio, and Alembic. Add development dependencies for pytest, pytest-asyncio, httpx, Ruff, and coverage. `Settings` must load `APP_ENV`, `DATABASE_URL`, `REDIS_URL`, `FRONTEND_ORIGINS`, `AI_MODE`, and deposit safety flags with the exact safe defaults from the specification. Add a valid empty Alembic environment whose script head is `None`; readiness treats database current revision `None` and script head `None` as aligned until T-04 creates revision `0001`.

- [ ] **Step 4: Implement envelopes and centralized errors**

```python
# backend/app/envelope.py
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class SuccessEnvelope(BaseModel, Generic[T]):
    ok: bool = True
    data: T
    meta: dict[str, object] | None = None

def ok(data: T, meta: dict[str, object] | None = None) -> SuccessEnvelope[T]:
    return SuccessEnvelope(data=data, meta=meta)
```

`ProductError` must map to `{"ok": false, "error": {"code", "message", "details"}}` without wrapping an existing envelope again. Register handlers for product errors, request validation errors, and unexpected exceptions; unexpected responses use code `INTERNAL_ERROR` and do not include exception text.

- [ ] **Step 5: Implement liveness and readiness dependency checks**

`/health/live` returns immediately. `/health/ready` executes `SELECT 1`, Redis `PING`, and an Alembic current/head comparison. Return 200 with component statuses only when all checks pass; otherwise return 503 with `NOT_READY` and component names, never connection strings.

- [ ] **Step 6: Add the backend Compose service and root commands**

Build from `python:3.12-slim`, install the package with development dependencies for local Compose, mount backend source read-only except caches, depend on healthy PostgreSQL and Redis, and expose port 8000. Add `backend:lint`, `backend:test`, and `backend:ready` root scripts. Expand pre-push to run Ruff and `pytest -m "not live"` through the backend container. Replace the initial Python lint-staged commands with `node scripts/ruff_staged.mjs`; the wrapper strips the leading `backend/` from staged paths and calls `docker compose run --rm backend ruff check --fix ...` followed by `ruff format ...`, ensuring hooks use Python 3.12 even when the host Python differs.

- [ ] **Step 7: Verify unit and live readiness behavior**

Run: `docker compose build backend`  
Run: `docker compose run --rm backend ruff check .`  
Run: `docker compose run --rm backend python -m pytest -q`  
Run: `docker compose up -d --wait postgres redis minio backend`  
Run: `Invoke-RestMethod http://localhost:8000/health/live`  
Run: `Invoke-RestMethod http://localhost:8000/health/ready`  
Expected: lint and tests pass; both endpoints return 200 and readiness reports database, Redis, and migration checks.

- [ ] **Step 8: Commit T-03 and record progress**

Commit implementation as `feat(backend): T-03 add service skeleton and health checks`, then record the short hash and passing checks in `docs/PROGRESS.md` and commit as `docs(progress): record T-03 completion`.

## Task 4: T-04 Initial Identity and Profile Migration

**Files:**

- Create: `backend/app/domains/identity/models.py`
- Create: `backend/app/domains/profiles/models.py`
- Create: `backend/app/platform/model_base.py`
- Create: `backend/app/platform/uuid7.py`
- Modify: `backend/migrations/env.py`
- Modify: `backend/migrations/script.py.mako`
- Create: `backend/migrations/versions/0001_identity_profiles.py`
- Create: `backend/tests/repository/test_initial_migration.py`
- Create: `backend/tests/unit/test_uuid7.py`
- Modify: `backend/app/platform/db.py`
- Modify: `docs/PROGRESS.md`

**Interfaces:**

- Consumes: SQLAlchemy async engine and Alembic configuration from T-03.
- Produces: `new_uuid7() -> UUID`; tables `users`, `profiles`, `skills`, `profile_skills`, `profile_languages`, and `availability_rules`; Alembic revision `0001`.

- [ ] **Step 1: Write failing UUID and migration tests**

```python
# backend/tests/unit/test_uuid7.py
from app.platform.uuid7 import new_uuid7

def test_uuid7_is_monotonic_and_versioned() -> None:
    first, second = new_uuid7(), new_uuid7()
    assert first.version == 7
    assert second.version == 7
    assert first.int < second.int
```

`test_initial_migration.py` must create a fresh temporary database, run `alembic upgrade head`, assert all six tables plus `alembic_version`, run `alembic downgrade base`, and assert the six domain tables are gone.

- [ ] **Step 2: Run tests and confirm missing schema failures**

Run: `docker compose run --rm backend python -m pytest tests/unit/test_uuid7.py tests/repository/test_initial_migration.py -q`  
Expected: FAIL because UUID generation and revision `0001` are absent.

- [ ] **Step 3: Add SQLAlchemy models with explicit constraints**

Use UUID primary keys and UTC timestamps. Implement:

- `users`: CITEXT unique email, status enum check, default locale, timestamps.
- `profiles`: PERSON or TEAM, optional owner constrained for PERSON, name length 1–80, bio length at most 2,000, locale, timezone, optional city, status, positive version, timestamps, partial unique PERSON owner index.
- `skills`: unique normalized name and display name length 1–80.
- `profile_skills`: profile/skill unique pair, optional non-negative years, verification status `UNVERIFIED|PENDING|VERIFIED`.
- `profile_languages`: profile/language unique pair, ISO two-letter language and proficiency `BASIC|CONVERSATIONAL|PROFESSIONAL|NATIVE`.
- `availability_rules`: profile, weekday 0–6, local start/end time with start before end, IANA timezone, unique rule position per profile.

- [ ] **Step 4: Write the reversible Alembic revision**

The upgrade must create `citext` and `vector`, then tables in dependency order. The downgrade must remove tables in reverse dependency order and leave shared extensions installed. Add named check constraints and indexes so later tests can target them deterministically.

- [ ] **Step 5: Verify upgrade, downgrade, and readiness**

Run: `docker compose exec -T backend alembic upgrade head`  
Run: `docker compose exec -T backend alembic downgrade base`  
Run: `docker compose exec -T backend alembic upgrade head`  
Run: `docker compose run --rm backend python -m pytest tests/unit/test_uuid7.py tests/repository/test_initial_migration.py -q`  
Run: `Invoke-RestMethod http://localhost:8000/health/ready`  
Expected: both migration directions and tests pass; final database is at head; readiness returns 200.

- [ ] **Step 6: Commit T-04 and record progress**

Commit implementation as `feat(database): T-04 add identity and profile schema`, then record the short hash and migration round-trip result in `docs/PROGRESS.md` and commit as `docs(progress): record T-04 completion`.

## Task 5: T-05 Next.js Skeleton, Tokens, Demo Frame, and Four Tabs

**Files:**

- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/postcss.config.mjs`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/page.tsx`
- Create: `frontend/app/demo/page.tsx`
- Create: `frontend/app/home/page.tsx`
- Create: `frontend/app/find/page.tsx`
- Create: `frontend/app/chat/page.tsx`
- Create: `frontend/app/done/page.tsx`
- Create: `frontend/app/globals.css`
- Create: `frontend/styles/tokens.css`
- Create: `frontend/components/shell/mobile-shell.tsx`
- Create: `frontend/components/shell/tab-bar.tsx`
- Create: `frontend/components/shell/icons.tsx`
- Create: `frontend/components/demo/demo-surface.tsx`
- Create: `frontend/components/demo/foundation-page.tsx`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/p0-mobile-shell.spec.ts`
- Modify: `package.json`
- Create: `.github/workflows/ci.yml`
- Modify: `docs/PROGRESS.md`

**Interfaces:**

- Consumes: exact design tokens and demo HTML stored by T-01.
- Produces: frontend scripts `dev`, `build`, `lint`, `typecheck`, `test`, and `test:e2e`; `MobileShell`; `TabBar`; `/demo`; exact CSS custom properties from §4.2.

- [ ] **Step 1: Write failing mobile shell E2E assertions**

```ts
// frontend/e2e/p0-mobile-shell.spec.ts
import { expect, test } from "@playwright/test";

test.use({ viewport: { width: 720, height: 900 } });

test("demo frame carries exact tokens and four destinations", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByTestId("demo-phone")).toHaveCSS("width", "400px");
  await expect(page.getByRole("navigation").getByRole("link")).toHaveCount(4);
  const brand = await page
    .locator("html")
    .evaluate((node) => getComputedStyle(node).getPropertyValue("--brand").trim());
  expect(brand).toBe("#17223A");
});
```

- [ ] **Step 2: Scaffold Next.js and confirm E2E failure**

Install `next@15`, `react@19`, `react-dom@19`, Tailwind CSS 4, TypeScript, Vitest, Testing Library, and Playwright in the frontend workspace. Run `pnpm --filter frontend test:e2e`; expected failure is a missing `/demo` implementation.

- [ ] **Step 3: Port exact tokens and global typography rules**

`tokens.css` must define every §4.2 variable verbatim. `globals.css` must apply Pretendard fallbacks, IBM Plex Mono only to numeric/hash helpers, `word-break: keep-all` for Korean, light color scheme, border-box sizing, and no Inter import. Define semantic utility classes without hardcoded colors outside the token file.

- [ ] **Step 4: Implement the mobile shell and tab contract**

```ts
// frontend/components/shell/tab-bar.tsx
export const tabs = [
  { id: "home", href: "/home", icon: "home" },
  { id: "find", href: "/find", icon: "search" },
  { id: "crew", href: "/chat", icon: "crew" },
  { id: "history", href: "/done", icon: "history" },
] as const;
```

Render four accessible links with monochrome inline SVGs, 68px fixed bottom navigation, active state, and a content bottom inset. Do not render fake device status text in `MobileShell`. Add `/home`, `/find`, `/chat`, and `/done` foundation pages using one `FoundationPage` component so every tab destination returns 200 and the actual app shell can be tested at a 390px viewport without the demo frame.

- [ ] **Step 5: Implement the demo-only phone frame**

`/demo` wraps `MobileShell` in a 400×820 black frame with 48px outer radius and 40px screen radius, matching the reference HTML. Mark it `data-testid="demo-phone"`. Keep this wrapper out of `/home`, `/find`, `/chat`, and `/done`.

- [ ] **Step 6: Add CI and verify the skeleton**

Run: `pnpm --filter frontend lint`  
Run: `pnpm --filter frontend typecheck`  
Run: `pnpm --filter frontend test`  
Run: `pnpm --filter frontend build`  
Run: `pnpm --filter frontend exec playwright test e2e/p0-mobile-shell.spec.ts`  
Expected: all checks pass and the mobile screenshot visually matches the token/frame/navigation portions of the source demo.

- [ ] **Step 7: Commit T-05 and record progress**

Commit implementation as `feat(frontend): T-05 add tokenized mobile shell`, then record the short hash, build, and screenshot test result in `docs/PROGRESS.md` and commit as `docs(progress): record T-05 completion`.

## Task 6: T-06 Shared Demo-Derived UI Components

**Files:**

- Create: `frontend/components/ui/button.tsx`
- Create: `frontend/components/ui/chip.tsx`
- Create: `frontend/components/ui/card.tsx`
- Create: `frontend/components/ui/row.tsx`
- Create: `frontend/components/ui/avatar.tsx`
- Create: `frontend/components/ui/section-heading.tsx`
- Create: `frontend/components/ui/section-gap.tsx`
- Create: `frontend/components/ui/note.tsx`
- Create: `frontend/components/ui/fold.tsx`
- Create: `frontend/components/ui/index.ts`
- Create: `frontend/app/dev/components/page.tsx`
- Create: `frontend/components/ui/ui-contract.test.tsx`
- Create: `frontend/e2e/p0-components.spec.ts`
- Modify: `docs/PROGRESS.md`

**Interfaces:**

- Consumes: CSS tokens and global typography from T-05.
- Produces: typed primitives `Button`, `Chip`, `Card`, `Row`, `Avatar`, `SectionHeading`, `SectionGap`, `Note`, and `Fold`; `/dev/components` visual catalog.

- [ ] **Step 1: Write failing component contracts**

```tsx
// frontend/components/ui/ui-contract.test.tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { Button, Fold } from "./index";

it("a disabled button never invokes its action", () => {
  let calls = 0;
  render(
    <Button disabled onClick={() => (calls += 1)}>
      Disabled
    </Button>,
  );
  fireEvent.click(screen.getByRole("button"));
  expect(calls).toBe(0);
});

it("the native fold reveals its content when toggled", () => {
  render(<Fold summary="Why">Evidence</Fold>);
  const summary = screen.getByText("Why");
  expect(screen.getByText("Evidence")).not.toBeVisible();
  fireEvent.click(summary);
  expect(screen.getByText("Evidence")).toBeVisible();
});
```

- [ ] **Step 2: Run unit tests and confirm missing exports**

Run: `pnpm --filter frontend test -- ui-contract.test.tsx`  
Expected: FAIL because the primitives do not exist.

- [ ] **Step 3: Implement typed primitives with exact contracts**

Use `Button` variants `primary|ghost` and sizes `default|small`, always retaining a 1.5px transparent border. Use `Chip` tones `verified|ai|warning|danger|neutral|outline`. `Avatar` accepts neutral palette index 1–6. `SectionHeading` must not export or use a `.sec` button class. `Fold` uses native `details/summary`. `Note` supports warning and informational presentation without emoji icons.

- [ ] **Step 4: Build the visual catalog**

Render every component variant and dangerous pairing at `/dev/components`: primary next to ghost button, all chip tones, all six avatars, long Korean and English row text, open/closed fold, section heading next to section gap, and warning note. Add stable `data-testid` attributes for height and overflow measurements.

- [ ] **Step 5: Add Playwright layout assertions**

At widths 360 and 414, assert primary/ghost paired buttons differ in height by 0px, no catalog element has unhandled `scrollWidth > clientWidth`, the fold toggles, and the page contains no images or emoji-based icons.

- [ ] **Step 6: Run the component gate**

Run: `pnpm --filter frontend test -- ui-contract.test.tsx`  
Run: `pnpm --filter frontend exec playwright test e2e/p0-components.spec.ts`  
Run: `pnpm --filter frontend lint && pnpm --filter frontend typecheck`  
Expected: unit, interaction, overflow, and equal-height checks pass.

- [ ] **Step 7: Commit T-06 and record progress**

Commit implementation as `feat(ui): T-06 add shared demo-derived primitives`, then record the short hash and component gate results in `docs/PROGRESS.md` and commit as `docs(progress): record T-06 completion`.

## Task 7: T-47 Locale Routing, Message Parity, and Language Switch

**Files:**

- Create: `frontend/i18n/config.ts`
- Create: `frontend/i18n/request.ts`
- Create: `frontend/i18n/routing.ts`
- Create: `frontend/middleware.ts`
- Create: `frontend/messages/ko.json`
- Create: `frontend/messages/en.json`
- Create: `frontend/components/shell/locale-switcher.tsx`
- Create: `frontend/app/[locale]/layout.tsx`
- Create: `frontend/app/[locale]/page.tsx`
- Create: `frontend/app/[locale]/demo/page.tsx`
- Create: `frontend/app/[locale]/home/page.tsx`
- Create: `frontend/app/[locale]/find/page.tsx`
- Create: `frontend/app/[locale]/chat/page.tsx`
- Create: `frontend/app/[locale]/done/page.tsx`
- Create: `scripts/check_i18n_parity.mjs`
- Create: `scripts/tests/i18n_parity.test.mjs`
- Create: `frontend/e2e/p0-locale.spec.ts`
- Modify: `frontend/next.config.ts`
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: `package.json`
- Modify: `.husky/pre-push`
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/PROGRESS.md`

**Interfaces:**

- Consumes: route-neutral shell and UI primitives.
- Produces: locales `ko|en`; `routing`; `LocaleSwitcher`; `/ko/*` and `/en/*`; `pnpm check:i18n`.

- [ ] **Step 1: Write failing parity and locale-preservation tests**

```js
// scripts/tests/i18n_parity.test.mjs
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const flatten = (value, prefix = "") =>
  Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return child && typeof child === "object" ? flatten(child, path) : [path];
  });

test("Korean and English message keys are identical", async () => {
  const ko = JSON.parse(await readFile("frontend/messages/ko.json", "utf8"));
  const en = JSON.parse(await readFile("frontend/messages/en.json", "utf8"));
  assert.deepEqual(flatten(en).sort(), flatten(ko).sort());
});
```

Playwright must start on `/ko/demo`, switch to English, assert `/en/demo`, reload, and assert the English selection remains active.

- [ ] **Step 2: Run tests and confirm missing locale files**

Run: `node --test scripts/tests/i18n_parity.test.mjs`  
Run: `pnpm --filter frontend exec playwright test e2e/p0-locale.spec.ts`  
Expected: FAIL because locale routing and messages are absent.

- [ ] **Step 3: Add next-intl routing and canonical redirects**

Define `locales = ["ko", "en"] as const`, default locale `ko`, and locale prefix `always`. Root `/` redirects to `/ko`. The locale layout validates the parameter with `hasLocale`, sets `<html lang>`, loads messages, and provides `NextIntlClientProvider`. Unsupported locale returns 404.

- [ ] **Step 4: Move every visible string into parity-checked messages**

Create matching `navigation`, `demo`, `components`, and `locale` namespaces. Korean is the source copy and English is a complete translation. The language switcher uses route replacement, preserves the path after the locale segment, and stores preference in the next-intl locale cookie.

- [ ] **Step 5: Enforce parity and hardcoded-copy linting**

`check_i18n_parity.mjs` recursively compares leaf key sets and prints keys missing from each file before exiting 1. Add `check:i18n` to root scripts, pre-push, and CI lint. Confirm the ESLint JSXText Korean selector fails against a temporary fixture exercised by a Node test and succeeds after all visible strings use `useTranslations` or `getTranslations`.

- [ ] **Step 6: Run locale verification**

Run: `pnpm check:i18n`  
Run: `pnpm --filter frontend lint`  
Run: `pnpm --filter frontend typecheck`  
Run: `pnpm --filter frontend build`  
Run: `pnpm --filter frontend exec playwright test e2e/p0-locale.spec.ts`  
Expected: parity, lint, type, build, switch, persistence, and both locale routes pass.

- [ ] **Step 7: Commit T-47 and record progress**

Commit implementation as `feat(i18n): T-47 add Korean and English routing`, then record the short hash and locale checks in `docs/PROGRESS.md` and commit as `docs(progress): record T-47 completion`.

## Task 8: T-48 Responsive AppShell and Desktop Navigation

**Files:**

- Create: `frontend/components/shell/app-shell.tsx`
- Create: `frontend/components/shell/desktop-shell.tsx`
- Create: `frontend/components/shell/side-nav.tsx`
- Create: `frontend/components/shell/chat-shell.tsx`
- Create: `frontend/components/shell/shell.module.css`
- Create: `scripts/check_page_responsive_boundary.mjs`
- Create: `scripts/tests/responsive_boundary.test.mjs`
- Create: `frontend/e2e/p0-responsive-shell.spec.ts`
- Modify: `frontend/components/shell/mobile-shell.tsx`
- Modify: `frontend/app/[locale]/layout.tsx`
- Modify: `frontend/app/[locale]/demo/page.tsx`
- Modify: `package.json`
- Modify: `.husky/pre-push`
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/PROGRESS.md`

**Interfaces:**

- Consumes: one route list, locale-aware links, and shared UI content.
- Produces: `AppShell({children, activeTab})`; `ChatShell({list, messages, assistant})`; CSS breakpoint contracts at 768, 1024, and 1440px; root command `check:responsive-boundary`.

- [ ] **Step 1: Write failing responsive ownership and E2E tests**

```js
// scripts/tests/responsive_boundary.test.mjs
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import test from "node:test";

test("page components contain no viewport branching", () => {
  const output = execFileSync("node", ["scripts/check_page_responsive_boundary.mjs"], {
    encoding: "utf8",
  });
  assert.match(output, /0 responsive violations/);
});
```

Playwright loops through widths 390, 768, 1024, and 1440. It asserts bottom tabs at 390/768, side navigation and no bottom tabs at 1024/1440, content max width, card max width 640px, and three chat columns only at 1440.

- [ ] **Step 2: Run tests and confirm missing desktop shell failure**

Run: `node --test scripts/tests/responsive_boundary.test.mjs`  
Run: `pnpm --filter frontend exec playwright test e2e/p0-responsive-shell.spec.ts`  
Expected: FAIL because `AppShell`, responsive scanner, and desktop layout do not exist.

- [ ] **Step 3: Implement one shared navigation model and shell containers**

`AppShell` renders both semantic navigation containers and lets CSS choose visibility; it does not call `window.matchMedia` or a viewport hook. `SideNav` reuses the same four route IDs and SVG components as `TabBar`. At desktop active state uses a 4px brand bar and brand-colored label. Main content is at most 960px and list/card content at most 640px.

- [ ] **Step 4: Implement chat layout promotion**

Below 1440px, render the assistant content inline with messages. At 1440px, use CSS grid columns `280px minmax(0, 1fr) 320px`. The message composer remains immediately below the message area, and its guard panel remains immediately above it. No page component receives a viewport or form-factor prop.

- [ ] **Step 5: Add the responsive boundary scanner**

Scan `frontend/app/**/{page,layout}.tsx` and `frontend/components/feature/**/*.tsx` for `matchMedia`, `innerWidth`, `useMediaQuery`, `isMobile`, `isDesktop`, and Tailwind responsive prefixes. Allow responsive CSS only in `components/shell` and stylesheets. Print exact file/line violations and exit 1 when found.

- [ ] **Step 6: Capture and verify all four breakpoint screenshots**

Run: `pnpm check:responsive-boundary`  
Run: `pnpm --filter frontend lint && pnpm --filter frontend typecheck`  
Run: `pnpm --filter frontend exec playwright test e2e/p0-responsive-shell.spec.ts --update-snapshots`  
Run again without `--update-snapshots`.  
Expected: 390, 768, 1024, and 1440 screenshots pass; page scan reports zero violations; desktop has no phone frame or fake status bar.

- [ ] **Step 7: Run the complete P0 gate**

Run: `pnpm verify:pre-push`  
Run: `docker compose config --quiet`  
Run: `docker compose up -d --wait`  
Run: `docker compose exec -T backend alembic upgrade head`  
Run: `Invoke-RestMethod http://localhost:8000/health/ready`  
Expected: all root, frontend, backend, infrastructure, migration, locale, and responsive checks pass.

- [ ] **Step 8: Commit T-48 and record P0 completion**

Commit implementation as `feat(shell): T-48 add responsive desktop shell`, then record the short hash and complete P0 gate in `docs/PROGRESS.md` and commit as `docs(progress): record T-48 and P0 completion`.

## P0 Exit Criteria

- T-01, T-02, T-03, T-04, T-05, T-06, T-47, and T-48 each have a passing implementation commit and a progress record.
- `pnpm verify:pre-push` exits zero without bypassing hooks.
- Docker Compose starts PostgreSQL with pgvector, Redis, MinIO, and the backend as healthy services.
- Empty-database Alembic upgrade, downgrade, and re-upgrade pass.
- `/health/live` and `/health/ready` return the expected distinct contracts.
- `/ko/demo` and `/en/demo` build and render.
- Mobile, tablet, desktop, and wide-chat shell screenshots pass.
- Shared components meet the HTML-derived token and sizing contracts.
- No page or feature component contains viewport branching.
- `docs/PROGRESS.md` contains the exact resume point for P1.
