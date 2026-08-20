# README Runtime Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the root README's placeholder local-command section with a copy-ready development and runtime guide.

**Architecture:** Keep the guide in the repository root `README.md`, because that is the document rendered by GitHub. Derive every command and version from the checked-in package manifests, Compose file, and environment example; do not change application behavior or the user's existing `package.json` edits.

**Tech Stack:** Markdown, Node.js 22–24, pnpm 11.19.0, Docker Compose v2, FastAPI/Alembic, Next.js 15.

## Global Constraints

- The final user-facing document is the repository root `README.md`.
- Install workspace dependencies with pnpm 11.19.0; do not recommend plain `npm install`.
- Preserve unrelated working-tree changes, especially `package.json`.
- Warn that `docker compose down -v` permanently removes local PostgreSQL, Redis, and MinIO volumes.

---

### Task 1: Publish the development command guide

**Files:**

- Modify: `README.md`

**Interfaces:**

- Consumes: `package.json` scripts, `frontend/package.json` scripts, `.env.example`, and `docker-compose.yml` service names and ports.
- Produces: GitHub-rendered setup, run, migration, verification, shutdown, and troubleshooting instructions.

- [x] **Step 1: Replace the placeholder command section**

Add prerequisites and a quick start containing these exact command flows:

```powershell
npm install --global pnpm@11.19.0
pnpm install --frozen-lockfile
Copy-Item .env.example .env
pnpm infra:up
docker compose run --rm backend alembic upgrade head
docker compose up -d --build --wait backend
pnpm --filter frontend dev
```

Also document Corepack as an alternative, service URLs, focused commands, production frontend commands, verification, ordinary shutdown, destructive reset, and Windows `EPERM` troubleshooting.

- [x] **Step 2: Verify formatting and Compose syntax**

Run:

```powershell
pnpm exec prettier --check README.md
docker compose config --quiet
git diff --check -- README.md
```

Expected: all commands exit with code 0.

- [x] **Step 3: Review the isolated diff**

Run:

```powershell
git diff -- README.md
git status --short
```

Expected: the README contains all approved sections, and the unrelated `package.json` modification remains untouched.
