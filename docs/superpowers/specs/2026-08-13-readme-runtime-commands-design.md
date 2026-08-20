# README 런타임 명령 문서 설계

**작성일:** 2026-08-13  
**범위:** 루트 `README.md`의 로컬 설치·실행·검증·종료 명령

## 목표

새 개발자가 저장소를 받은 뒤 별도 설명 없이 의존성을 설치하고, 환경변수를 준비하고, Docker 인프라와 백엔드를 실행하고, 데이터베이스를 최신 마이그레이션으로 올리고, 프론트엔드를 시작할 수 있게 한다. 문서의 모든 명령은 현재 `package.json`, `frontend/package.json`, `docker-compose.yml`, `.env.example`에 실제로 존재하는 계약만 사용한다.

## 선택한 구성

README에 짧은 **빠른 시작**과 목적별 **상세 명령 모음**을 함께 둔다. 빠른 시작만 제공하면 문제 해결과 운영 명령이 부족하고, 상세 참조만 제공하면 최초 실행 순서를 놓치기 쉽다. 두 구성을 함께 두되 같은 명령을 불필요하게 반복하지 않는다.

이 저장소는 `packageManager: pnpm@11.19.0`인 pnpm workspace이므로 `npm i`를 정본으로 안내하지 않는다. Node.js 22 이상 25 미만에서 `corepack enable`, `corepack prepare pnpm@11.19.0 --activate`, `pnpm install --frozen-lockfile` 순서로 설치한다. 루트의 사용자 소유 untracked `package-lock.json`은 README 작업에 포함하거나 삭제하지 않는다.

## 문서 구조

1. **사전 요구사항:** Node.js 22~24, Corepack, Docker Desktop 또는 Docker Engine과 Compose v2.
2. **5분 빠른 시작:** 저장소 루트 이동, pnpm 활성화, 의존성 설치, `.env` 생성, Compose 전체 실행, Alembic 적용, 프론트 개발 서버 실행.
3. **접속 주소:** 프론트 `http://localhost:3000`, 백엔드 `http://localhost:8000`, OpenAPI `http://localhost:8000/docs`, readiness `http://localhost:8000/health/ready`, MinIO Console `http://localhost:9001`.
4. **목적별 명령:** 인프라만 실행, backend 포함 전체 실행, 상태·로그·readiness, migration, 프론트 개발/production build·start, lint·test·Playwright·전체 pre-push.
5. **종료와 초기화:** 일반 종료는 데이터를 유지하고, `docker compose down -v`는 PostgreSQL·Redis·MinIO 볼륨을 삭제한다는 경고와 함께 별도 위험 구역에 둔다.
6. **문제 해결:** 포트 충돌, migration readiness 실패, Docker 이미지 재빌드, 설치 상태 복구에 필요한 최소 명령만 둔다.

PowerShell과 POSIX 셸에서 다른 `.env` 복사 명령은 둘 다 제시한다. 나머지 pnpm·Docker 명령은 공통 코드 블록으로 유지한다.

## 실행 순서와 책임

Compose는 PostgreSQL, Redis, MinIO, FastAPI backend를 실행한다. 프론트 개발 서버는 호스트의 별도 터미널에서 실행한다. 최초 또는 migration 변경 후에는 backend readiness 전에 `docker compose run --rm backend alembic upgrade head`를 실행한다. `docker compose up -d --build --wait backend`는 backend와 필수 의존성을 빌드·시작하고 health 상태까지 기다린다.

production 형태의 프론트 확인은 `pnpm --filter frontend build` 후 `pnpm --filter frontend start`로 안내한다. 개발 중에는 `pnpm --filter frontend dev`를 사용한다.

## 오류·안전 안내

- `APP_ENV=development`, `AI_MODE=stub`, 로컬 인증 키는 개발 전용임을 명시한다.
- 운영 환경에서는 `.env.example`의 비밀값을 사용할 수 없으며, JWT 키는 최소 32바이트의 안전한 값이어야 한다.
- `docker compose down`은 컨테이너와 네트워크만 내리고 볼륨은 유지한다.
- `docker compose down -v`는 로컬 데이터 전체 삭제 명령이므로 복구 불가 경고를 바로 앞에 둔다.
- 설치 문제 해결에 `pnpm install --frozen-lockfile`을 우선하며, pnpm lockfile과 혼용되는 `npm install`은 사용하지 않는다.

## 검증

문서 수정 후 다음을 확인한다.

- README의 모든 npm/pnpm/Docker 명령이 현재 스크립트와 Compose 서비스에 존재한다.
- `pnpm exec prettier --check README.md`와 `git diff --check`가 통과한다.
- `docker compose config --quiet`가 통과한다.
- 설치 이후의 핵심 명령인 `pnpm verify:pre-push`가 통과한다.
- README 변경만 stage하며 사용자 소유 `package-lock.json`은 untracked 상태로 보존한다.
