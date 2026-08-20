# PANGAEA 결정 기록

명세에 직접 정해지지 않은 구현 판단과 그 근거를 기록합니다.

## D-001 태스크 커밋과 진행 기록

- 결정: 각 태스크 구현을 먼저 커밋하고, 생성된 짧은 커밋 해시를 `docs/PROGRESS.md`에 기록하는 문서 커밋을 바로 뒤에 남긴다.
- 근거: 하나의 커밋 안에는 자기 자신의 최종 해시를 기록할 수 없다. 구현 커밋과 진행 기록 커밋을 연속으로 두면 명세의 태스크별 복구 가능성과 정확한 인계 정보를 모두 만족한다.

## D-002 개발 브랜치

- 결정: P0는 격리 작업공간의 `feature/T-01-foundation` 브랜치에서 구현한다.
- 근거: 명세의 `feature/* → develop → main` 흐름을 지키고 초기 `main`을 변경하지 않는다.

## D-003 Git 훅의 pnpm 실행

- 결정: Husky 훅은 `.husky/pnpm` 래퍼를 통해 pnpm을 실행한다. POSIX에서는 `pnpm`, Windows Git Bash에서는 `pnpm.cmd`를 선택한다.
- 근거: Codex Windows 런타임은 `pnpm.cmd`만 제공해 명세의 `pnpm` 명령을 Git Bash가 찾지 못한다. 실행 대상과 인자는 그대로 유지하면서 세 훅이 실제로 동작하도록 환경 차이만 격리한다.

## D-004 의존성 빌드 스크립트 허용 범위

- 결정: pnpm `allowBuilds`에서 `esbuild`, `sharp`, `unrs-resolver` 세 패키지만 허용한다.
- 근거: 현재 Next.js·Vite 툴체인의 설치와 빌드에 필요한 패키지다. 미등록 패키지는 pnpm의 `strictDepBuilds` 기본 차단을 유지하며 전체 빌드 스크립트 허용 옵션은 사용하지 않는다.

## D-003 2026-08-18 세션 — 데모 슬라이스 완성 방침 (사용자 지시 반영)

- 결정: SPEC §0 실행 프롬프트(태스크별 TDD 커밋·46태스크 순차·검수 에이전트 루프)는 사용자 지시로 **적용하지 않는다**. 명세의 기술 계약(§2 불변 규칙, §4 디자인, §5~§7 데이터·API·AI 게이트)만 청사진으로 따른다.
- 결정: 검증은 **로컬호스트 전용**(Vercel 배포 없음). 이 맥엔 Docker가 없어 Homebrew pg16+pgvector(소스빌드)·redis 네이티브 스택으로 구동하고, 훅·readiness는 Docker 부재 시 venv 폴백을 쓴다.
- 결정: 번역 프로바이더는 OpenAI Responses API(`TRANSLATE_PROVIDER=openai`, 키는 서버 전용). 키가 없으면 결정적 스텁 — 데모 fixture 문장만 번역되고 나머지는 원문 발신+「번역 확인 필요」 칩(§2.4-3의 화면 시연이기도 하다). Papago는 키 발급 불가로 제외.
- 결정: AI 라이브 경로는 번역만 우선 구현. parse/guard/lens/why/search는 결정적 스텁이 정식 동작이며(키 없이 전 화면), OpenAI 라이브 확장은 후속 작업으로 남긴다.
- 결정: 신뢰 온도 데모 시드는 `trust_events`에 `DEMO_SEED` 이벤트(행에 delta 저장)로 표현한다. §4.6-A의 is_demo 노출과 §5.7 공식 재현(37.3→38.5)을 동시에 만족하는 방법이다.
- 결정: WebSocket 대신 채팅 5초 폴링. 팀 프로필(S08)·업로드/자격(S07 일부)·운영자 콘솔은 이번 슬라이스에서 제외(시드로 TEAM 프로필 1건만 존재). 보증금 화면(S10)은 별도 페이지 대신 마무리 화면에 인라인.
- 결정: 필드 암호화(BYTEA ciphertext)·outbox·idempotency 테이블은 로컬 데모 범위에서 생략. 멱등성은 `client_message_id`·`provider_event_id` UNIQUE로 보장.
- 결정: 가드 수정안에 결정적 `rewritten_text`를 추가(호칭 정규식 치환·줄임말 사전 확장). 리라이트가 불가능한 규칙(완곡 보류 등)은 조언만 표시하고 「바꿔서 보내기」 버튼을 숨긴다 — 조언 문장이 그대로 전송되던 결함의 수정.
- 결정: 구 P0 셸 E2E(placeholder 기준)는 실앱 기준 `demo-slice.spec.ts`로 교체. 로그인 레이트리밋(10회/10분) 때문에 Playwright는 setup 프로젝트에서 API 로그인 1회 후 storageState를 공유한다.
