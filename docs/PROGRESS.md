# PANGAEA 진행 기록

다음 세션은 마지막 완료 항목 다음 태스크부터 시작합니다. 완료 줄 형식은 다음과 같습니다.

```text
- [x] T-07 프로필/스킬 API — 2026-08-13 · 커밋 abc1234 · 테스트 12 pass
```

## P0 기반

- [x] T-01 레포 초기화 · 워크스페이스 · Git 훅 — 2026-08-13 · 커밋 7719761 · 행동 테스트 2 pass, 훅 검증 3 pass
- [x] T-02 Docker Compose 인프라 — 2026-08-13 · 커밋 9a9c9c0 · Compose 계약 1 pass, pgvector·Redis·MinIO 라이브 검증 통과
- [x] T-03 FastAPI 스켈레톤 · 공통 봉투 · 헬스체크 — 2026-08-13 · 커밋 c5d1e36 · Python 5 pass, Ruff·live·ready 통과
- [x] T-04 초기 데이터베이스 마이그레이션 — 2026-08-13 · 커밋 e446190 · Python 7 pass, 빈 DB upgrade·downgrade·readiness 통과
- [x] T-05 Next.js 스켈레톤 · 토큰 · 모바일 셸 — 2026-08-13 · 커밋 9f0e20e · Next build·Playwright 1 pass·스크린샷 검증 통과
- [x] T-06 공통 UI 컴포넌트 — 2026-08-13 · 커밋 1732c55 · Vitest 2 pass, Playwright 2 pass, 360/414px 스냅샷·Next build·전체 pre-push 검증 통과
- [x] T-47 i18n 골격 — 2026-08-13 · 커밋 ee5e188 · 번역 키 48개 동등성, JSX 한글 하드코딩 거부, Playwright 5 pass, ko/en 정적 빌드 통과
- [x] T-48 데스크톱 셸 — 2026-08-13 · 구현 52ce7ef · 리뷰 수정 b696ee5 · Playwright 11 pass, 4개 브레이크포인트·채팅 2/3단 스냅샷, 반응형 위반 0건, 전체 P0 게이트 통과

> **2026-08-18 갱신** — 사용자 지시로 §0 태스크 절차 대신 데모 슬라이스를 한 번에 완성했다(아래 체크박스는 이 시점 이후 관리하지 않는다).
> 백엔드 43개 API 경로 + `pangaea_ai` 레이어 + 시드 + 96 pytest, 프런트 13개 화면(ko/en·모바일/데스크톱·PWA) + 11 Playwright E2E가 로컬에서 전부 통과.
> 세부 판단은 docs/DECISIONS.md D-003, 실행법은 README를 본다.

## P1 인증·프로필

- [x] T-07 가입 · 로그인 · refresh 회전 · 재사용 탐지 — 2026-08-13 · 구현 468fdd2·e636152·e5533bb·3b602bb · 보안 수정 d45eac8·e319c08·efcfd12·8ed20fc · backend 65 pass, root 7 pass, UI 2 pass, Playwright 11 pass, Ruff·Compose·Alembic·readiness·전체 pre-push 통과
- [ ] T-08 권한 컨텍스트 · IDOR 가드
- [ ] T-09 개인 프로필 CRUD
- [ ] T-10 업로드 · 자격 · 포트폴리오
- [ ] T-11 팀 프로필
- [ ] T-12 인증·프로필 프론트

## P2 AI 레이어 뼈대

- [ ] T-13 AI 패키지 · 클라이언트 · 봉투
- [ ] T-14 live/replay/stub 모드
- [ ] T-15 strict Pydantic 스키마
- [ ] T-16 AI 게이트 5종
- [ ] T-17 결정적 폴백
- [ ] T-18 모더레이션 · 자해 분기
- [ ] T-19 문화 KB · 검색

## P3 시그널

- [ ] T-20 요청 파서
- [ ] T-21 파서 백엔드 어댑터
- [ ] T-22 시그널 DRAFT · revision
- [ ] T-23 발행 게이트
- [ ] T-24 시그널 작성 프론트
- [ ] T-25 홈 · 시그널 상세 프론트

## P4 검색·추천

- [ ] T-26 검색 정규화 · 프로필 검색
- [ ] T-27 결정적 추천 실행
- [ ] T-28 추천 이유
- [ ] T-29 추천 · 프로필 · 직접 찾기 프론트

## P5 지원·협업·보증금

- [ ] T-30 지원 · 초대 · 수락
- [ ] T-31 협업 상태 머신
- [ ] T-32 보증금 합의
- [ ] T-33 sandbox provider · 원장
- [ ] T-34 보증금 문구
- [ ] T-35 지원 · 초대 · 보증금 프론트

## P6 채팅

- [ ] T-36 발신 전 가드
- [ ] T-37 번역
- [ ] T-38 메시지 발신 오케스트레이션
- [ ] T-39 문화 렌즈 · WebSocket
- [ ] T-40 채팅 · 근거 프론트

## P7 완료·평가·신뢰

- [ ] T-41 완료 · 환급 · 신뢰 이벤트
- [ ] T-42 trust.v1 projection
- [ ] T-43 마무리 · 평가 · 알림 프론트

## P8 마감

- [ ] T-44 AI 평가셋
- [ ] T-45 하드 실패 스캐너
- [ ] T-46 시드 · replay · README · 데모 각본
- [ ] T-49 영문 문구 전수 검증
- [ ] T-50 폼팩터 × 언어 E2E
