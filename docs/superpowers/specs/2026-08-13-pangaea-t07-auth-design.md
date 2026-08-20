# PANGAEA T-07 인증 설계

**작성일:** 2026-08-13  
**범위:** 가입, 로그인, refresh 회전, 재사용 탐지, 로그아웃  
**근거:** `docs/SPEC.md` §1.5-E, §6.1, §6.2, §6.7, §6.8, §9.1, T-07

## 목표와 비목표

이 작업은 이메일과 비밀번호로 계정을 만들고 로그인한 뒤, 15분 access token과 30일 refresh token으로 세션을 유지하는 인증 기반을 만든다. refresh token은 사용할 때마다 교체하며, 이미 사용한 토큰이 다시 제출되면 같은 token family 전체를 즉시 폐기한다. 로그인 시도는 IP당 10회/10분으로 제한한다.

개인 프로필 생성과 `acting_profile_id` 권한 컨텍스트는 각각 T-09와 T-08의 범위다. 소셜 로그인은 구현하지 않고 교체 가능한 `IdentityProvider` 포트만 둔다. 비밀번호 재설정, 이메일 인증, 다중 인증, WebSocket 1회용 토큰도 이번 범위에 포함하지 않는다.

## 선택한 접근

refresh token은 암호학적 난수인 불투명 토큰으로 발급하고 서버에는 SHA-256 해시만 저장한다. refresh JWT에 `jti`를 넣어도 재사용 탐지를 위해 DB 상태가 필요하므로 얻는 이점이 없고, 세션마다 현재 해시 하나만 저장하면 이전 토큰의 재사용과 알 수 없는 토큰을 구분할 수 없다. 따라서 각 회전 이력을 별도 행으로 보존하는 방식을 사용한다.

refresh token은 `HttpOnly`, `SameSite=Lax`, `/api/v1/auth` 경로의 쿠키로 전달한다. 운영 환경에서는 `Secure`를 강제한다. access token만 성공 응답의 JSON 데이터에 포함한다. 이 구조는 브라우저 JavaScript에서 장기 토큰을 읽지 못하게 하면서 T-12의 새로고침 후 세션 복원을 지원한다.

## 구성 요소와 경계

- `platform/crypto.py`: Argon2id 비밀번호 해시·검증, refresh 난수 생성·해시, access JWT 인코딩을 담당한다. 원문 비밀번호와 토큰을 저장하거나 기록하지 않는다.
- `domains/identity/repository.py`: 사용자, 비밀번호 자격, 세션, refresh 행의 영속화와 회전 트랜잭션을 담당한다. refresh 행 조회에는 `SELECT ... FOR UPDATE`를 사용한다.
- `domains/identity/service.py`: 가입·로그인·refresh·로그아웃 유스케이스와 제품 오류 매핑을 담당한다. HTTP 쿠키나 FastAPI 타입에는 의존하지 않는다.
- `domains/identity/providers.py`: 향후 소셜 공급자가 구현할 `IdentityProvider` 프로토콜을 정의한다.
- `api/v1/auth.py`: 요청 검증, 클라이언트 IP 추출, rate limit, 쿠키 입출력, 성공 봉투를 담당한다.
- `platform/rate_limit.py`: Redis에서 원자적 sliding-window 제한을 수행한다. 키에는 IP의 HMAC/해시 표현만 사용해 원문 PII를 남기지 않는다.

각 계층은 스키마와 프로토콜로 연결한다. 서비스 단위 테스트는 저장소와 시계를 대체할 수 있고, 실제 PostgreSQL 잠금·제약·마이그레이션은 저장소 및 통합 테스트에서 검증한다.

## 데이터 모델

기존 `users`에는 `token_version INTEGER NOT NULL DEFAULT 1 CHECK (token_version > 0)`을 추가한다.

`password_credentials`는 `user_id`를 기본키이자 `users` 외래키로 사용하고 `password_hash`, 생성·갱신 시각을 저장한다. 인증 방법을 사용자 행과 분리해 이메일 로그인 구현이 향후 `IdentityProvider`와 결합되지 않게 한다.

`auth_sessions`의 한 행이 하나의 token family다. `id`, `user_id`, 발급 당시 `token_version`, `expires_at`, `revoked_at`, `revocation_reason`, 생성·갱신 시각을 저장한다. 정지·삭제 사용자 또는 폐기된 세션에는 새 토큰을 발급하지 않는다.

`refresh_tokens`는 `id`, `session_id`, 고유한 `token_hash`, `expires_at`, `consumed_at`, `revoked_at`, `replaced_by_token_id`, 생성 시각을 저장한다. 원문 토큰은 응답 쿠키를 구성하는 동안에만 메모리에 존재한다. `session_id`와 활성 상태에 필요한 인덱스를 둔다.

## API 계약

모든 경로는 `/api/v1` 아래에 있고 기존 성공·오류 봉투를 사용한다.

- `POST /auth/register`: `email`, `password`, `default_locale`를 받아 사용자를 만들고 201로 access token과 사용자 식별자를 반환하며 refresh 쿠키를 설정한다. 이메일 중복은 `AUTH_EMAIL_ALREADY_REGISTERED` 409다.
- `POST /auth/login`: `email`, `password`를 받아 200으로 같은 세션 응답을 반환한다. 사용자 부재, 틀린 비밀번호, 비활성 사용자는 모두 `AUTH_INVALID_CREDENTIALS` 401로 통일한다.
- `POST /auth/refresh`: 요청 본문 없이 refresh 쿠키를 소비해 새 access token과 교체된 refresh 쿠키를 반환한다. 알 수 없거나 만료·폐기된 토큰은 `AUTH_INVALID_CREDENTIALS` 401이다. 이미 소비된 토큰이면 family를 폐기한 뒤 `AUTH_SESSION_REUSED` 401이다.
- `POST /auth/logout`: 제시된 refresh token의 family를 폐기하고 쿠키를 지운다. 쿠키가 없거나 이미 무효여도 성공하는 멱등 동작으로 처리한다.

성공 데이터는 `user_id`, `access_token`, `token_type="Bearer"`, `expires_in=900`만 노출한다. refresh token과 비밀번호 해시는 응답·오류 상세·로그에 포함하지 않는다. 비밀번호는 12~128자로 제한하고 이메일은 공백을 제거한 뒤 CITEXT 정본을 사용한다. 지원 locale은 현재 프론트와 같은 `ko`, `en`이다.

## 토큰과 회전 흐름

access JWT는 HS256으로 서명하며 제품 claim은 `sub`, `session_id`, `token_version`만 둔다. `iat`, `exp`는 표준 수명 검증용 claim이다. 서명 키, access TTL, refresh TTL, cookie 보안 설정은 환경 설정으로 주입한다.

정상 refresh는 하나의 DB 트랜잭션에서 다음 순서로 처리한다.

1. 제출 토큰을 해시하고 해당 `refresh_tokens` 행을 잠근다.
2. 세션·사용자 상태와 토큰 만료·폐기 여부를 확인한다.
3. `consumed_at`이 이미 있으면 세션과 family 전체를 폐기하고 재사용 오류를 반환한다.
4. 새 refresh 행을 삽입하고 기존 행에 `consumed_at`과 `replaced_by_token_id`를 기록한다.
5. 커밋 후 새 refresh 원문은 쿠키로, 새 access token은 응답 데이터로 전달한다.

동일 토큰의 동시 요청은 행 잠금으로 직렬화된다. 첫 요청만 회전에 성공하고, 두 번째 요청은 소비 상태를 확인해 새로 생긴 토큰까지 포함한 family를 폐기한다.

## Rate limit과 오류 처리

로그인은 프록시 신뢰 설정이 명시되지 않은 현재 단계에서는 소켓 peer IP를 기준으로 제한한다. 임의의 `X-Forwarded-For`는 신뢰하지 않는다. Redis Lua 스크립트가 최근 10분의 시도 시각을 정리하고 현재 요청을 추가하는 작업을 원자적으로 수행한다. 열한 번째 요청은 `RATE_LIMITED` 429와 `Retry-After`를 반환한다. Redis 장애는 명세의 인프라 장애 규칙에 따라 503으로 변환한다.

예상 가능한 인증 실패는 `ProductError`로 안전한 고정 메시지만 반환한다. DB unique 충돌은 이메일 값을 노출하지 않고 제품 오류로 변환한다. 예외, 토큰, 이메일, 비밀번호는 로그에 남기지 않는다.

## 검증 전략

- 단위: Argon2id 검증, refresh 원문/해시 분리, JWT claim·만료, 서비스의 일반 로그인 실패 통합, 정상 회전, 재사용 family 폐기, 로그아웃 멱등성.
- 저장소: 빈 DB에서 `0002` upgrade/downgrade, 제약·인덱스, 회전 연결 관계, family 일괄 폐기.
- 통합: 가입과 로그인 성공, 중복 가입, 잘못된 로그인, 쿠키 속성, refresh 교체, 이전 토큰 재사용 후 새 토큰도 거부, 로그아웃 후 refresh 거부, 10회/10분 제한.
- 회귀: Ruff, 전체 backend pytest, 루트 `verify:pre-push`, Docker Compose migration/readiness를 다시 실행한다.

T-07 완료의 결정적 증거는 이전 refresh token을 재사용한 요청이 `AUTH_SESSION_REUSED`를 반환하고, 그 직전에 발급된 replacement token도 이후 `AUTH_INVALID_CREDENTIALS`로 거부되는 통합 테스트다.
