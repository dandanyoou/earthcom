# 0. 이 문서를 읽는 AI에게 — 실행 프롬프트 (가장 먼저 읽고, 이대로 작동할 것)

```prompt
너는 PANGAEA를 처음부터 끝까지 혼자 만들어 내는 시니어 풀스택 구현자다.
이 문서는 너의 유일한 정본(source of truth)이다. 이 문서에 없는 기능은 만들지 않고,
이 문서에 있는 기능은 하나도 빠뜨리지 않는다.

[역할]
- 너는 제안하는 사람이 아니라 완주하는 사람이다. 확인을 구하지 말고 합리적 기본값으로 진행한다.
- 비가역적이거나 비용이 발생하는 결정(외부 결제 연동 활성화, 유료 API 키 발급, main 브랜치 강제 푸시)만
  사람에게 묻는다. 그 외의 판단은 네가 내리고, 내린 가정을 PROGRESS.md에 기록한다.

[읽는 순서]
1) §0 이 프롬프트  2) §1 범위와 스택  3) §2 불변 규칙  4) 담당 파트(§3~§9)
5) §11 테스트 차단선  6) §13 작업 분해  7) §14 검수 게이트
문서가 서로 충돌하면 §1.4의 우선순위표를 따른다. 표에 없는 충돌은 §1.5 해소 표를 따른다.

[작업 방식 — 반드시 지킬 것]
1. 기능은 최소 단위로 쪼갠다. §13의 태스크(T-01…T-46)를 순서대로 하나씩 처리한다.
   한 태스크는 "한 번의 커밋으로 되돌릴 수 있는 크기"여야 한다. 여러 태스크를 묶어 커밋하지 않는다.
2. 만들면 반드시 테스트한다. 태스크마다 §13에 적힌 DoD와 테스트를 작성·실행하고,
   통과할 때까지 고친 뒤에만 다음 태스크로 넘어간다. 통과 전 "완료" 보고 금지.
3. 태스크 하나가 끝날 때마다 즉시 커밋하고 원격에 푸시한다. 그리고 docs/PROGRESS.md에 한 줄 남긴다.
   토큰 한도·세션 종료로 작업이 끊겨도, 다음 세션이 PROGRESS.md만 읽고 이어받을 수 있어야 한다.
   푸시가 불가능한 환경이면 로컬 커밋 + PROGRESS.md 기록만으로도 반드시 남긴다.
4. 커밋 전에 `git add -A` 후 `git -c core.quotepath=false diff --cached --stat`으로
   새 파일이 실제로 스테이징됐는지 눈으로 확인한다. 폴더명은 전부 소문자로 쓴다.
5. Husky · Prettier · ESLint를 반드시 설치·활성화한다(§12.3). 훅을 --no-verify로 건너뛰지 않는다.
6. 브랜치는 feature/* → PR → develop 순서로 간다. main은 사람이 명시적으로 지시할 때만 건드린다.

[불변 규칙 — 코드로 강제되어야 하며, 어기면 CI가 머지를 막는다]
- AI는 표현만 한다. 판정(점수·순위·신뢰 지표·보증금 금액·과실·역할 설계)에 절대 손대지 않는다.
- 역할(roles_requested)은 요청자가 폼에 직접 쓴 것만 저장한다. AI가 만든 역할은 스키마상 표현 불가능하다.
- 근거(KB ID)가 없으면 문화 주석을 발행하지 않는다. 침묵이 추측보다 낫다.
- 앱은 작업 대금에 관여하지 않는다. 보증금(위약금)만 다루며 정산·지분·비율 필드는 만들지 않는다.
- 스키마를 통과하지 못한 모델 응답은 폐기하고 결정적 폴백을 쓴다. 모델 원문이 화면에 직행하는 경로는 없다.
- OPENAI_API_KEY는 서버 프로세스에만 존재한다. 프론트 번들에 들어가면 CI가 막는다.
- API 키가 하나도 없어도(AI_MODE=stub) 전체 테스트와 전체 화면이 돌아가야 한다.

[디자인]
- 화면의 정본은 §4의 디자인 시스템과 원본 목업 `PANGAEA_데모_수정.html`이다.
  색·간격·컴포넌트·카피 톤을 그대로 계승한다. 임의로 보라색 그라데이션, Inter 폰트,
  균일한 카드 그리드 같은 AI 기본값으로 갈아타지 않는다.
- 화면 문구에 개발 내부 용어(L1/L3/M1/degraded/스키마/모듈명)를 절대 노출하지 않는다.
  목업이 이미 그렇게 만들어져 있고, 그게 이 제품의 태도다.
- 모바일과 데스크톱 웹을 둘 다 만든다. 모바일이 정본이고 데스크톱은 §4.7의 셸만 갈아 끼운다.
  화면을 두 벌 만들지 않는다 — 페이지 컴포넌트는 자기가 어느 폼팩터에 있는지 몰라야 한다.
- UI는 한국어·영어 2종(next-intl)이다. JSX에 한글을 직접 쓰지 않고 messages/*.json에서 가져온다.
  ja·de·pt는 UI 언어가 아니라 메시지 번역·문화 주석의 대상 언어다.

[완료 판정]
§14의 검수 에이전트 3종을 모두 띄워, 셋 다 PASS를 낼 때까지 고친다.
- 에이전트 1: 명세·인터뷰 대비 본질 이탈(요구되지 않은 기능, 불변 규칙 위반, 누락) 점검
- 에이전트 2: 모든 버튼과 그 하위 페이지까지 실제 동작 E2E 점검
- 에이전트 3: 고아 문자·고아 줄바꿈·겹침·잘림·대비 등 디자인 QA
하나라도 FAIL이면 수정 후 세 에이전트를 다시 전부 돌린다. 부분 통과로 종료하지 않는다.
최종 보고는 결론(무엇을 만들었고 무엇이 통과했나) 먼저, 근거는 뒤에 쓴다.
```

---

**문서명**: PANGAEA 통합 개발 명세서 v1.0
**병합 원본**: `기능정리.md` v0.1 · `AI레이어_개발명세서_v2.0.md` · `백엔드_api.md` v1.0 · `데이터DB_명세서_v0.2.md` · `PANGAEA_데모_수정.html`
**작성일**: 2026-08-13
**상태**: 구현 착수용 확정본

---

# 1. 제품 정의와 이번 빌드의 범위

## 1.1 한 줄 정의

> 인증된 사람을 미리 등록해 두고, 필요한 사람이 생기면 국경과 상관없이 그중에서 매칭·추천받는 서비스.

네 개의 국경을 넘는 것이 제품의 전부다.

| 국경 | 대응 기능 | 책임 |
|---|---|---|
| 01 지리 | 조건 기반 자동 추천, 현지 체류가 필요한 요청의 위치 플래그, UTC 겹침 시간 | 결정적 코드 |
| 02 언어 | 받은 메시지 직역 + 보낸 메시지 의도 보존 번역 | AI |
| 03 문화 | 오해·금기 표현 사전 경고, 근거를 인용한 문화 주석 | AI |
| 04 조직 | 개인 프로필과 팀(밴드형) 프로필이 같은 경로로 매칭 | 프로필 구조 |

## 1.2 이번 빌드의 범위 — 데모 수직 슬라이스

**포함한다 (전부 실제로 동작해야 한다).**

가입 → 프로필·스킬 등록 → 시그널 작성(파싱 미리보기 + 역할 직접 입력) → 발행 → 자동 추천 + 직접 검색 → 지원/초대 → 수락 → 협업 생성 → 보증금 합의·예치(sandbox) → 채팅(발신 전 확인 · 발신 번역 · 문화 도우미) → 완료 확인 → 보증금 환급 → 상호 평가 → 신뢰 온도 갱신.

**포함하지 않는다 (인터페이스만 남기고 비활성).**

| 항목 | 처리 |
|---|---|
| 운영자 콘솔(자격 검토 큐·모더레이션 큐·분쟁 결의 화면) | API와 권한 검사는 구현, 화면은 만들지 않음. 시드 스크립트로만 조작 |
| 실제 금전 이동 | `DEPOSIT_PROVIDER=sandbox` 고정. production 어댑터는 `NotImplementedError` |
| 과실 귀속(FORFEIT_TO_COUNTERPART) | `DEPOSIT_FORFEITURE_ENABLED=false`. 상태 머신과 테스트만 존재 |
| 소셜 로그인 | `IdentityProvider` 포트만 정의. 이메일+비밀번호만 구현 |
| ko·en 외 UI 언어 | UI는 한국어·영어 2종만(§1.5-D). ja·de·pt는 **메시지 번역·문화 주석 대상 언어**이지 UI 언어가 아니다 |
| 푸시 알림 | 인앱 알림 목록까지. FCM/APNs 연동 없음 |
| 신조어 KB 승격 운영 화면 | `kb_candidates` 적재까지. 승격은 시드 스크립트 |

## 1.3 확정 스택

| 레이어 | 선택 | 비고 |
|---|---|---|
| 프론트 (E1) | Next.js 15 App Router · TypeScript · Tailwind CSS v4 | 목업의 CSS 변수를 디자인 토큰으로 이식 |
| 폼팩터 | **모바일 웹 + 데스크톱 웹 둘 다** | 모바일이 정본, 데스크톱은 §4.7 셸 규격 |
| 다국어 | `next-intl` · UI는 ko/en 2종 · 메시지 번역 대상은 ko·en·ja·de·pt 5개 언어권 | §4.8 |
| 백엔드 (E2) | FastAPI · Python 3.12 · SQLAlchemy 2.x · Pydantic v2 · Alembic | 모듈러 모놀리스 |
| AI (E3) | `pangaea_ai` 파이썬 패키지, E2 프로세스에 in-process 임포트 | 별도 서비스 아님 |
| LLM | OpenAI Responses API · Structured Outputs(strict) | 모델 ID는 env 한 곳에서만 |
| DB (E4) | PostgreSQL 16 + pgvector · Redis 7 | 임베딩 1536차원 고정 |
| 저장소 | MinIO (S3 호환) | 자격증·포트폴리오 원본 |
| 실행 | Docker Compose (postgres · redis · minio · backend) + `pnpm dev`(프론트) | |
| 형상 | 새 GitHub private 레포 `pangaea`, `feature/* → develop → main` | Husky·Prettier·ESLint 필수 |

## 1.4 문서 우선순위 (충돌 시)

```
기능정리 v0.1  >  이 통합 명세  >  AI 레이어 v2.0(E3 내부 계약)  >  백엔드 v1.0  >  데모 HTML  >  DB v0.2
(원안자 확정)      (본 문서)        (프롬프트·스키마·게이트 정본)     (API·상태 정본)   (디자인 정본)
```

단, 아래 두 가지는 예외적으로 각 문서가 정본이다.

- **화면의 색·간격·컴포넌트·카피 톤** → 데모 HTML이 정본. 이 문서가 다르게 쓰여 있으면 HTML을 따른다.
- **모델 선택·프롬프트 문안·출력 스키마·근거 게이트** → AI 레이어 v2.0이 정본. 본 문서는 그것을 복제·요약했을 뿐이며, 수정하지 않는다.

## 1.5 이 명세가 해소한 문서 간 충돌 8건

원본 문서 다섯 개가 서로 다른 말을 하던 지점이다. 구현자는 **여기 적힌 결론만** 따르면 된다.

| # | 충돌 | 원본이 서로 다르게 말한 내용 | **이 명세의 결론** | 근거 |
|---|---|---|---|---|
| A | 신뢰 온도 | HTML은 37.3°·41.2°를 숫자로 표시하고 완료 후 37.3→38.5로 오름. 백엔드는 `trust_indicator_enabled=false`, `value=null`, `UNAVAILABLE`. 기능정리는 계산식 ⛔미정 | **결정적 `trust.v1` 공식을 실제로 구현한다**(§5.7). 값은 `trust_events`에서만 계산되고 LLM은 관여하지 않는다. `TRUST_POLICY_VERSION=disabled`면 UNAVAILABLE 경로로 폴백한다(기본값은 `trust.v1`) | 기능정리 §5는 "게임화 지표" 방향만 확정하고 식을 금지하지 않았다. 완료 +1.2가 HTML의 37.3→38.5, 41.2→42.4를 그대로 재현한다 |
| B | 추천 순서 설명 패널 | HTML은 가중치(기술 34%·신뢰온도 22%·시간대 20%·언어 14%·인증 10%)를 보여줌. 백엔드 `matching.v1`은 가중합이 아닌 **사전식 정렬**이고 신뢰 지표는 정렬 키에 없음 | **접힘 패널 UI·문구·"문화나 국적은 이 계산에 들어가지 않아요" 한 줄은 그대로 유지하고, 막대 그래프를 사전식 우선순위 목록으로 교체**한다(§4.6-B). 신뢰 온도는 "순서 계산에 쓰지 않고 카드에 참고용으로만 표시"라는 한 줄을 추가한다 | 화면이 서버가 실제로 하는 일과 달라지면 심사에서 그 자리가 곧 약점이 된다. 디자인(접힘 패널)은 HTML 기준, 내용(정렬 규칙)은 기능·백엔드 기준 |
| C | 매칭에 문화가 들어가는가 | 목업 문구는 "문화나 국적은 계산에 안 들어감", ADR-001도 동일 | 그대로 유지. `matching.v1` 정렬 튜플에 문화 거리·국적·AI confidence·신뢰값·보증금 금액을 넣지 않는다. CI가 검사한다 | ADR-001 |
| D | UI 언어 | HTML은 한국어 전용, 제품 컨셉은 국경 넘는 매칭 | **`next-intl`로 ko/en 전환을 넣는다.** 한국어는 100%, 영어는 전 화면 필수. 화면에 하드코딩된 문자열은 0건이며 전부 `messages/{ko,en}.json`에서 온다. ja·de·pt는 UI 언어가 아니라 **번역·주석 대상 언어**다 | 국경을 넘는 서비스가 한국어로만 뜨면 컨셉과 화면이 어긋난다. 심사에서 영어 전환 한 번이 04 조직·02 언어 국경의 증거가 된다 |
| D-2 | 폼팩터 | 목업은 400×820 폰 프레임만 있고 데스크톱 레이아웃이 없음 | **모바일과 데스크톱 웹을 둘 다 만든다.** 모바일(360–430px)이 정본이고, ≥1024px에서는 §4.7의 데스크톱 셸(좌측 세로 내비 + 넓은 콘텐츠, 대화는 3단)로 전환한다. 토큰·컴포넌트·문구는 완전히 공유하고 셸만 갈아 끼운다 | 사용자 확정. 데스크톱 전용 디자인을 새로 만드는 게 아니라 **같은 컴포넌트를 다른 셸에 담는다**는 점이 중요하다 |
| E | 로그인 수단 | 기능정리는 "이메일/소셜", 백엔드는 provider allowlist만 정의 | **이메일+비밀번호만 구현.** Argon2id · access 15분 · refresh 30일 회전 · 재사용 탐지까지 명세대로. 소셜은 `IdentityProvider` 포트만 남긴다 | OAuth 앱 등록이 외부 계정 작업이라 자동 실행 불가 |
| F | `compensation.amount_krw` 이름과 통화 | AI 파서는 `amount_krw`인데 currency enum에 USD·JPY·EUR가 있음 | **E2 어댑터에서 `amount_minor` + `currency`로 변환**하고 환율 변환은 하지 않는다. 외부 API는 `amount_minor`만 노출한다. `currency='NONE'`이면 금액은 반드시 null | 백엔드 §3.3 |
| G | `skills[].importance` 숫자 | AI가 0~1 점수를 내는데 "AI는 점수 판정 금지" 원칙과 충돌 | **불확실성 메타데이터로만 취급.** 저장·화면 표시·검색·추천·신뢰 계산 어디에도 쓰지 않고 parse trace 만료(30분)와 함께 폐기한다. CI가 유입 경로를 검사한다 | 백엔드 §14, ADR-002 |
| H | 목업의 "AI 역할 자동 설계" | 구 목업에 있던 기능. 기능정리 §3에서 채택하지 않음 | **이미 해소됨.** 새 데모 HTML은 「필요한 역할 · 직접 정하기」 + `＋ 역할 추가`로 교체되어 있고 칩 색도 AI(파랑)가 아니다. 이 상태를 정본으로 구현한다 | 데모 HTML 399~408행 |

---

# 2. 불변 규칙 — 코드로 강제한다

## 2.1 AI가 하는 일 / 절대 하지 않는 일

| AI가 **하는** 일 (표현) | AI가 **절대 안 하는** 일 (판정) |
|---|---|
| 자연어 → 스키마 구조화 | 매칭 점수·순위 결정 |
| 요청자가 **명시한** 역할을 구조화 | 역할 설계·제안 |
| 받은 메시지 직역 + 근거를 인용한 문화 주석 | 신뢰 온도 계산 |
| 보낸 메시지 의도 보존 번역 | 보증금 금액·상한 산정 |
| 오해·금기 **경고**와 수정안 제시 | 과실 100% 판정 |
| 추천 이유 **문장 골격** 작성 (숫자는 슬롯) | 자격 인증 검증·배지 발급 |
| 검색 질의어 정규화·동의어 확장 | 검색 결과 순위 |
| 신조어·관용구 탐지 | 발신 **차단** (경고까지만) |

## 2.2 ADR-002를 강제하는 4겹

1. **입력 차단** — 판정 수치는 프롬프트에 들어가지 않는다. E2는 `{{slot}}` **이름만** 넘기고, 실제 값은 AI 응답을 받은 **뒤** 결정적 코드가 치환한다. 모델이 본 적 없는 숫자는 바꿔 쓸 수 없다.
2. **스키마 봉쇄** — 모든 AI 출력 스키마에 점수·순위·금액·지표 필드가 존재하지 않는다. `roles_requested[].origin`은 enum이 `["EXPLICIT"]` 단일값이라 AI가 만든 역할은 물리적으로 표현 불가능하다.
3. **발행 직전 린트** — AI 산출 문자열에 `{{...}}` 밖의 아라비아 숫자, `₩`·`원`·`점`·`위`·`°`·`%` 패턴이 있으면 해당 문장을 폐기하고 결정적 폴백으로 바꾼다.
4. **CI 차단** — §11.3의 하드 실패 조건. 하나라도 걸리면 머지 불가.

## 2.3 미정 규칙 비의존 원칙

기능정리가 의도적으로 미정(⛔)·잠정(🟡)으로 남긴 6개 항목에 **AI 레이어는 하나도 의존하지 않는다.**

| 미정 항목 | 의존하지 않는 방법 |
|---|---|
| 신뢰 지표 계산식 | AI 문장에 `{{indicator}}` 슬롯을 아예 제공하지 않는다. 슬롯이 없으면 언급할 문법적 수단이 없다 |
| 매칭 가중치 | 추천 이유는 "왜 이 후보인가"만 서술. 순위·점수는 언급 대상이 아니다 |
| 인증 검토 방식 | 파서는 `required_credentials`를 **탐지만** 한다. 필터링 여부는 서버 정책 |
| 과실 판정 주체 | 보증금 문구는 "누가 판정하는가"를 서술하지 않는다. 조건 요약만 |
| 모임 매칭 방식 | `signal_type=CIRCLE`이면 역할 배열이 비어 있어도 유효 |
| 보증금 적용 범위 | `deposit_applies` 불리언을 서버에서 받는다. 스스로 판단하지 않는다 |

## 2.4 서비스 전체에 걸린 원칙 6개

1. **차단하지 않는다** — 가드가 HIGH를 내도 발신 버튼은 살아 있다. 경고이지 검열이 아니다.
2. **침묵한다** — 근거가 없으면 문화 주석을 달지 않는다. 폴백으로 대충 채우지 않는다(문화 주석과 번역만 폴백이 "없음"이다).
3. **숨기지 않는다** — 번역에 실패하면 원문을 병기해 보내고 그 사실을 칩으로 표시한다. 조용히 틀린 번역을 내보내지 않는다.
4. **비지 않는다** — AI가 죽어도 화면은 비지 않는다. 결정적 폴백 결과와 "간이 모드" 배지를 보여준다.
5. **돈에 손대지 않는다** — 앱이 다루는 돈은 보증금뿐이다. 작업 대금은 당사자끼리.
6. **처벌하지 않는다** — 경고를 무시하고 보낸 이력은 크루 로그에만 남고 신뢰 지표에 반영하지 않는다.

---

# 3. 사용자 흐름과 화면 목록

## 3.1 End-to-End 흐름

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 55, "rankSpacing": 60, "padding": 14, "useMaxWidth": true}}}%%
flowchart TB
    A["가입 · 로그인"] --> B["프로필 · 스킬 등록"]
    B --> C["시그널 작성"]
    C --> D["구조화 미리보기"]
    D --> E["발행 게이트"]
    E --> F["자동 추천"]
    E --> G["직접 검색"]
    F --> H["지원 · 초대"]
    G --> H
    H --> I["수락"]
    I --> J["보증금 합의 · 예치"]
    J --> K["채팅"]
    K --> L["완료 확인"]
    L --> M["보증금 환급"]
    M --> N["상호 평가"]
    N --> O["신뢰 온도 갱신"]
```

각 단계의 세부 규칙은 다음과 같다.

| 단계 | 세부 |
|---|---|
| 시그널 작성 | 자연어 한 줄 + **역할은 요청자가 폼에 직접 입력** |
| 구조화 미리보기 | 추정값(`INFERRED`)은 점선 배지, 사용자가 확인해야 다음으로 |
| 발행 게이트 | §6.4의 9개 조건을 모두 통과해야 `DRAFT → OPEN` |
| 수락 | 협업·멤버·기본 대화를 한 트랜잭션으로 생성 |
| 보증금 합의 | **WORK·BOOKING만.** HELP·CIRCLE은 이 단계를 건너뛰고 바로 채팅으로 간다 |
| 채팅 | 보내기 전 확인 · 발신 번역 · 문화 도우미 |
| 신뢰 온도 갱신 | 완료·평가 이벤트가 쌓인 뒤 결정적 계산(§5.7), 크루 해산 |

## 3.2 화면 목록과 하위 페이지 인벤토리

검수 에이전트 2가 이 표를 그대로 테스트 케이스로 쓴다. **"누르면 아무 일도 일어나지 않는 버튼"이 하나라도 있으면 FAIL이다.**

| ID | 화면 | 출처 | 진입점 | 이 화면의 모든 인터랙션 → 도달해야 할 곳 |
|---|---|---|---|---|
| S00 | 로그인 / 가입 | 신규 | 비로그인 시 전체 리다이렉트 | 로그인→S01 · 가입→S07 온보딩 · 비밀번호 규칙 오류 인라인 표시 |
| S01 | 홈 | HTML 318–374 | 탭 1 | 신뢰 온도 카드→S05 기록 · 「무슨 일에, 어떤 사람이 필요한가요?」→S02 · 「직접 찾아보기」→S06 · 유형 칩 4종(도움/일/모임/섭외)→목록 필터 적용 · 도시 스트립(가로 스크롤) · 주변 시그널 카드→S12 시그널 상세 |
| S02 | 시그널 올리기 | HTML 377–417 | S01 | 뒤로→S01 · 본문 입력→디바운스 후 「이렇게 이해했어요」 갱신 · 추정 태그(점선) 탭→S02a 수정 시트 · 역할 행 ✕→삭제 확인 · `＋ 역할 추가`→S02b 역할 입력 시트 · 2차 창작 안내→확인 체크 · 「시그널 올리고 사람 찾기」→발행 게이트→S03 |
| S02a | 추정값 수정 시트 | 신규(하위) | S02 점선 태그 | 값 수정·삭제·"맞아요" 확인 → S02로 복귀, 확인 시각 기록 |
| S02b | 역할 입력 시트 | 신규(하위) | S02 `＋ 역할 추가` | 역할명(1~40자)·인원(1~50 또는 미정) 입력 → S02 목록에 추가 |
| S03 | 추천 받은 사람 | HTML 420–490 | S02 발행 후 | 뒤로→S02 · 「순서는 어떻게 정해지나요?」 접힘→펼침 · 「프로필 보기」→S03a · 「함께하자고 하기」→S03b 초대 확인→S04 · 「나중에 보기」→카드 접힘 상태 저장 |
| S03a | 프로필 상세 | 신규(하위) | S03 · S06 | 스킬·언어·가능 시간·확인된 작업물·신뢰 온도·평가 목록. 「함께하자고 하기」→S03b |
| S03b | 초대 / 지원 확인 | 신규(하위) | S03 · S03a | 역할 선택 · 메시지 입력 → 지원/초대 생성 → 성공 시 S09 |
| S04 | 대화 | HTML 493–560 | 탭 3 · S03b | 뒤로→S03 · 말풍선 「원문 —」 토글 · 문화 도우미의 「왜 이렇게 알려주나요?」→S04a 근거 시트 · 입력창 타이핑(400ms 정지)→보내기 전 확인 패널 · 「그대로 보내기」/「바꿔서 보내기」→발신 후 배지 분기 · 번역 실패 시 「번역 확인 필요」 칩 + 원문 병기 |
| S04a | 근거 시트 | 신규(하위) | S04 「왜 이렇게 알려주나요?」 | KB 레코드 6필드(주장·언어권·맥락·출처 2건 이상·확인 날짜·확신도 강/보통/참고) + 「우리는 안 그래요」 이의 제기 버튼 |
| S05 | 마무리 | HTML 563–602 | 탭 4 · S01 온도 카드 | 뒤로→S04 · 결과물 4종 해시 표시 · 「보증금 환급」 상태 · 온도 변화 행 · 「평가 남기기」→S05a · 크루 해산 |
| S05a | 상호 평가 | 신규(하위) | S05 | POSITIVE/NEUTRAL/NEGATIVE + 태그 + 코멘트 → 제출 → S05 갱신 |
| S06 | 직접 찾기 | HTML 605–641 | 탭 2 · S01 | 검색어 입력→정규화 칩 표시 · 결과 행→S03a · 「23명 더 보기」→커서 페이지네이션 |
| S07 | 내 프로필 · 스킬 등록 | 신규 | 가입 직후 · S05 | 이름·소개·도시·언어·가능 시간 · 스킬 추가/삭제 · 포트폴리오 URL 등록 · 자격 제출(파일 업로드) |
| S08 | 팀 프로필 | 신규 | S07 | 팀 생성 · 멤버 초대(링크) · 팀 스킬 · 팀 명의로 지원 전환 |
| S09 | 받은 지원 / 보낸 지원 | 신규 | S01 알림 · S03b 이후 | 지원 카드→수락/거절/철회 · 수락 시 협업 생성 → S10 또는 S04 |
| S10 | 보증금 합의 | 신규 | S09 수락 후(WORK·BOOKING) | 금액 제안(상한 검증) · 조건 3줄 설명 · 동의 서명 · 예치(sandbox) → 전원 완료 시 S04 |
| S11 | 알림 | 신규 | 탭 없음(홈 상단 진입) | 알림 목록 · 읽음 처리 · 각 항목→해당 리소스 화면 |
| S12 | 시그널 상세 | 신규(하위) | S01 카드 | 원문·역할·조건·요청자 프로필 · 「지원하기」→S03b |

**모든 화면은 모바일과 데스크톱 두 폼팩터, ko·en 두 언어에서 각각 동작해야 한다.** 화면을 두 벌 만드는 것이 아니라 §4.7의 셸이 갈리는 것이며, 위 표의 "도달해야 할 곳"은 네 조합 모두에서 동일하다.

## 3.3 하단 탭 4개 (HTML 647–652 고정)

`홈 / 찾기 / 크루 / 기록`. 화면-탭 매핑은 목업 스크립트의 `TAB` 객체를 그대로 계승한다.
**데스크톱(≥1024px)에서는 같은 4항목이 좌측 세로 내비가 된다**(§4.7-1). 항목·아이콘·목적지는 완전히 동일하고 배치만 바뀐다.

```
home, write, who, s12  → 홈
find, s03a             → 찾기
chat, s10, s09         → 크루
done, s05a, s07, s08   → 기록
```

---

# 4. 디자인 시스템 — 정본은 `PANGAEA_데모_수정.html`

## 4.1 원칙

- 밝은 톤. 흰 배경 + 회색 위계 + 브랜드 1색. 국내 커뮤니티 앱 관례를 따른다.
- **데이터가 주인공이다.** 문화 도우미·경고 패널은 배경을 연하게, 여백을 좁게 눌러 메시지를 방해하지 않는다.
- 대비는 전 항목 WCAG AA 통과. 아래 토큰 주석의 대비값을 깨는 색 변경 금지.
- 이모지는 기기마다 컬러/무채색이 섞여 톤이 깨진다. 아이콘은 **단색 인라인 SVG**(stroke 1.7, linecap/linejoin round)로 통일한다. 국기 이모지 금지 — `.cc` 국가 코드 배지를 쓴다.

## 4.2 토큰 (그대로 이식)

```css
--bg:#FFFFFF; --bg2:#F7F8FA; --bg3:#FDF4E7;
--line:#EDEFF3; --line2:#DFE3EA;
--t1:#191F28;   /* 본문 16.6 */
--t2:#4E5968;   /* 보조 7.11 */
--t3:#6B7684;   /* 캡션 4.62 */
--brand:#17223A;      /* 버튼·주요 액션 15.83 */
--brand-l:#26364F;    /* 보조·테두리 12.19 */
--temp:#B4571E;       /* 신뢰 온도 숫자 4.86 */
--temp-bar:#E08A2E;   /* 온도 바 채움 — 배경 전용 */
--ok:#1C7A6E;   --ok-bg:#E7F4F1;
--info:#1F4E96; --info-bg:#EAF1FB;
--warn:#A05F0E; --warn-bg:#FDF3E2;
--dgr:#C0392B;  --dgr-bg:#FDECEA;
--kr:"Pretendard","Apple SD Gothic Neo","Malgun Gothic",sans-serif;
--mono:"IBM Plex Mono",ui-monospace,monospace;
```

색의 의미는 고정이다. **청록(`--ok`)=검증·결정적 코드 / 파랑(`--info`)=AI / 주황(`--warn`)=주의·문화 도우미 / 빨강(`--dgr`)=보내기 전 확인**. 아바타 색(`.av1`~`.av6`)은 의미가 없어야 하므로 채도를 낮춘 중립 세트를 쓴다.

## 4.3 타이포와 한글 조판

- 본문 `--kr`, 숫자·시각·해시만 `--mono`. **한글이 섞인 줄에 고정폭 글꼴을 쓰지 않는다** (자간이 깨진다 — 보증금 금액 `.dep .dv`가 이 이유로 sans다).
- `word-break: keep-all` 전역 적용. 어절 중간 분리 금지.
- **고아 문자 금지**: 마지막 줄에 한 글자만 남는 줄바꿈을 만들지 않는다. 필요하면 `&nbsp;`나 `<wbr>`로 묶는다. 검수 에이전트 3이 이걸 본다.
- 제목 letter-spacing은 `-.02em ~ -.035em`. 캡션은 조정하지 않는다.

## 4.4 컴포넌트 계약 (목업 CSS 주석에 남은 함정 4개를 그대로 승계)

| 컴포넌트 | 규칙 | 이유(목업 주석) |
|---|---|---|
| `.btn` 변형 | 모든 변형이 같은 높이가 되도록 기본값에 투명 테두리를 둔다 | 고스트 버튼과 나란히 놓았을 때 1.5px씩 어긋난다 |
| 보조 버튼 클래스 | `.btn.ghost`. **`.sec`를 보조 버튼 이름으로 쓰지 않는다** | 섹션 제목 규칙 `.sec`와 충돌해 margin이 붙는다 |
| 온도 바 | `span`은 inline이라 height가 무시된다. 바 요소는 반드시 `display:block` | 바가 사라진다 |
| 온도 바 클래스명 | `.tbar`/`.tfill`. **`.bar`를 쓰지 않는다** | 상단 앱바 `.bar`의 padding이 먹어 높이가 무너진다 |
| 채팅 입력창 | 스크롤 영역 밖(`.scr` 직계)에 `position:absolute; bottom:68px` | 안에 두면 콘텐츠 끝에 매달려 화면을 가린다 |
| 채팅 페이지 | `#p-chat { padding-bottom:74px }` | 하단 입력창 위로 확인 패널이 올라와야 한다 |

## 4.5 사용자 문구 규칙 (매우 중요)

화면에 **개발 내부 용어를 절대 쓰지 않는다.** 목업이 이미 전부 걷어낸 상태다.

| 내부 개념 | 화면 문구 |
|---|---|
| M1 파서 결과 | 「이렇게 이해했어요」 |
| `origin=INFERRED` | 「점선 표시는 직접 쓰지 않으셔서 짐작한 내용이에요. 눌러서 고칠 수 있어요.」 |
| roles_requested 폼 | 「필요한 역할」 + 칩 「직접 정하기」 (청록) |
| L1 직역 | 「원문 —」 |
| L3 문화 주석 | 「이렇게 읽으시면 좋아요」 / 「이런 뜻일 수 있어요」 |
| 확신도 3단 | 「자주 그래요」(강) / 「그런 편이에요」(보통) / 「가끔 그래요」(참고) + 점 3개 게이지 |
| KB 근거 시트 | 「왜 이렇게 알려주나요?」 |
| M3 가드 | 「보내기 전에 한 번만 확인해 주세요」 + 「이렇게 바꿔보세요」 |
| 가드 선택지 | 「그대로 보내기」 / 「바꿔서 보내기」 |
| `TRANSLATION_UNSAFE` | 칩 「번역 확인 필요」 + 「줄임말이 많아 번역이 어려웠어요 · 원문 그대로 전달됨」 |
| M4 번역 결과 | 「L. Weber는 이렇게 받았어요 —」 |
| `degraded=true` | 칩 「간이 모드」 (주황) |
| 보증금 | 「약속 보증금」 |
| 매칭 순위 | 「1순위」 / 「이런 분들이 있어요」 |

## 4.6 목업 대비 반드시 바꿔야 할 곳 2건

**A. 신뢰 온도 표시 (§1.5-A 결론 반영)**
카드의 숫자는 유지하되, 값의 출처는 `GET /profiles/{id}/trust`다. `status=UNAVAILABLE`이면 숫자 자리에 `—`와 「평가 데이터 집계 중」을 표시한다. 시드 데이터로 채운 값은 `is_demo=true`이며 개발 환경에서만 노출한다.

**B. 「순서는 어떻게 정해지나요?」 패널 (§1.5-B 결론 반영)**
접힘 UI·요약 문구·마지막 한 줄은 그대로 두고, 막대+퍼센트를 **번호가 붙은 우선순위 목록**으로 교체한다.

```
순서는 어떻게 정해지나요?
  1  기술이 맞는 정도
  2  필요한 역할과 이름이 겹치는 정도
  3  쓰는 언어
  4  시간대가 겹치는 정도
  5  확인된 작업물 수
  ─────────────────────────────
  문화나 국적은 이 계산에 들어가지 않아요.
  신뢰 온도도 순서에는 쓰지 않아요 — 카드에 참고용으로만 보여드려요.
```

이 목록은 `recommendation_runs.policy_version`이 정하는 값을 서버에서 내려받아 렌더한다. 프론트에 하드코딩하지 않는다.

## 4.7 데스크톱 셸 — 같은 컴포넌트, 다른 껍데기 (§1.5-D2)

**모바일이 정본이다.** 데스크톱은 새 디자인이 아니라 **같은 컴포넌트를 담는 다른 셸**이다. 토큰·타이포·컴포넌트·문구·상태 로직을 100% 공유하고, 갈아 끼우는 것은 내비게이션과 컨테이너뿐이다.

| 브레이크포인트 | 셸 | 규칙 |
|---|---|---|
| `< 768px` (모바일, **정본**) | 목업 그대로 | 하단 탭 4개 고정(68px) · 콘텐츠 폭 100% · 앱바 sticky |
| `768–1023px` (태블릿) | 모바일 셸 유지 | 콘텐츠를 `max-width:520px` 중앙 정렬, 좌우 여백만 확보. 레이아웃을 바꾸지 않는다 |
| `≥ 1024px` (데스크톱) | 2단 셸 | 좌측 세로 내비 `240px` + 콘텐츠 `max-width:960px`. **하단 탭은 사라지고 좌측 내비로 승격된다** |
| `≥ 1440px` (대화 화면만) | 3단 셸 | 대화 목록 `280px` + 메시지 영역 + 우측 근거·도우미 패널 `320px` |

데스크톱 전용 규칙:

1. **내비 승격** — 하단 탭의 4항목(홈·찾기·크루·기록)이 좌측 세로 내비가 된다. 아이콘 SVG와 라벨을 그대로 쓰고, 활성 상태만 `background: var(--t1); color:#fff` → 좌측 4px 브랜드 바 + `--brand` 텍스트로 바꾼다.
2. **카드 폭 상한** — 모든 카드(`.who`·`.post`·`.card`)의 최대 폭은 `640px`. 넓은 화면에서 카드가 가로로 늘어나 텍스트 줄 길이가 90자를 넘는 상황을 만들지 않는다.
3. **컬럼 늘리기 금지** — 데스크톱이라고 카드를 2열·3열 그리드로 깔지 않는다. 목록은 세로 한 줄을 유지한다. (균일 카드 그리드는 §4.1이 금지한 AI 기본값이다)
4. **대화 3단** — `≥1440px`에서 문화 도우미(`.help`)와 근거 시트(S04a)가 모달이 아니라 우측 고정 패널로 붙는다. `<1440px`에서는 모바일과 동일하게 메시지 흐름 안에 인라인으로 남는다.
5. **보내기 전 확인 패널** — 데스크톱에서도 모달이 아니라 입력창 바로 위 인라인 패널이다. 「그대로 보내기」가 항상 왼쪽. 폼팩터가 바뀌어도 "차단하지 않는다"는 원칙의 시각적 표현은 동일하다.
6. **폰 프레임 장식** — `.phone` 목업 프레임(`border-radius:48px`, 검은 베젤)은 **시연용 데모 페이지(`/demo`)에서만** 쓴다. 실제 앱 화면에는 넣지 않는다.
7. **상태바 위조 금지** — 목업의 `16:02 · KR 5G` 가짜 상태바는 실제 앱에 넣지 않는다. 데모 페이지 한정.

**구현 방식**: `app/(app)/layout.tsx` 하나에서 `AppShell`을 렌더하고, `AppShell`이 CSS 컨테이너 쿼리/미디어 쿼리로 `<MobileShell>` · `<DesktopShell>`을 고른다. **페이지 컴포넌트는 자기가 어느 셸에 있는지 알지 못한다.** 페이지가 폼팩터를 분기하기 시작하면 화면마다 두 벌을 유지해야 하고, 그 순간 목업과의 대조가 불가능해진다.

## 4.8 다국어 (ko / en) 조판 규칙 (§1.5-D)

- **하드코딩 문자열 0건.** 모든 화면 문구는 `messages/ko.json` · `messages/en.json`에서 온다. ESLint 규칙으로 JSX 안의 한글 리터럴을 금지한다.
- 한국어가 원본이고 영어가 번역본이다. **두 파일의 키 집합은 완전히 같아야 한다** — 불일치 시 CI 실패.
- **영어는 길다.** 한국어 대비 평균 1.3~1.6배로 늘어난다. 버튼·칩·탭 라벨은 en 기준으로 넘치지 않는지 확인한다. 특히 위험한 것: 「함께하자고 하기」→"Ask to work together" · 「보내기 전에 한 번만 확인해 주세요」 · 「약속 보증금 전액 돌려드려요」.
- 줄바꿈 처리는 언어별로 다르다. **ko는 `word-break: keep-all`**(어절 단위), **en은 `overflow-wrap: break-word`**. `<html lang>`에 따라 자동 분기한다.
- 숫자·날짜·통화는 `Intl.NumberFormat` / `Intl.DateTimeFormat`으로 locale 포맷팅한다. `300,000원` ↔ `KRW 300,000`. **금액 값 자체는 서버가 주는 `amount_minor`를 그대로 쓰고 프론트가 환산하지 않는다.**
- 신뢰 온도의 `°` 표기와 소수 1자리는 두 언어 공통이다.
- **UI 언어와 번역 대상 언어는 다른 축이다.** UI를 영어로 보는 한국인 사용자가 일본어 메시지를 받으면, UI는 en · 메시지 직역은 사용자의 `preferred_language`(ko) 기준으로 나간다. 이 둘을 같은 값으로 묶지 않는다.

---

# 5. 데이터 모델

## 5.1 ERD

```
users ──< profiles(kind=PERSON|TEAM) ──< team_memberships
profiles ──< profile_skills / profile_languages / availability_rules
profiles ──< credentials / portfolios
profiles ──< signals ──< signal_roles / signal_skills / signal_deliverables / signal_revisions
signals ──< applications ──> collaborations ──< collaboration_members
collaborations ──> conversations ──< messages ──< message_translations
messages ──< lens_annotations ;  conversations ──< guard_events
collaborations ──> deposit_agreements ──< deposit_parties / deposit_ledger_entries / deposit_resolutions
collaborations ──< completion_confirmations / reviews
profiles ──< trust_events / trust_snapshots
kb_norms (독립) · kb_candidates (독립)
signal_parse_runs(Redis) · outbox_events · audit_logs · idempotency_records · notifications
```

## 5.2 공통 규칙

- ID는 UUIDv7 문자열. 시각은 ISO 8601 UTC.
- 금액은 정수 minor unit + ISO 4217 통화 코드. KRW는 1원 = 1 unit.
- 민감 필드(요청 원문·메시지 원문·평가 코멘트)는 컬럼 암호화(`BYTEA` + 별도 hash 컬럼).
- 변경 가능한 aggregate에 정수 `version`. 불일치 시 409.
- `deposit_ledger_entries` · `trust_events` · `audit_logs` · `outbox_events`는 append-only. 런타임 DB role에 UPDATE/DELETE 권한을 주지 않는다.
- 마이그레이션은 Alembic으로만. 빈 DB에서 `alembic upgrade head`가 성공해야 한다.

## 5.3 핵심 DDL (발췌 — 나머지는 백엔드 명세 §6 그대로)

```sql
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
  id UUID PRIMARY KEY,
  email CITEXT NOT NULL UNIQUE,
  status TEXT NOT NULL CHECK (status IN ('ACTIVE','SUSPENDED','DELETION_PENDING','DELETED')),
  default_locale TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE profiles (
  id UUID PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('PERSON','TEAM')),
  owner_user_id UUID REFERENCES users(id) ON DELETE RESTRICT,
  display_name TEXT NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 80),
  bio TEXT NOT NULL DEFAULT '' CHECK (char_length(bio) <= 2000),
  locale TEXT NOT NULL, timezone TEXT NOT NULL, city_code TEXT,
  status TEXT NOT NULL CHECK (status IN ('DRAFT','ACTIVE','HIDDEN','SUSPENDED')),
  version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK ((kind='PERSON' AND owner_user_id IS NOT NULL) OR kind='TEAM')
);
CREATE UNIQUE INDEX uq_person_profile_owner
  ON profiles(owner_user_id) WHERE kind='PERSON' AND status <> 'SUSPENDED';

CREATE TABLE signals (
  id UUID PRIMARY KEY,
  requester_profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  signal_type TEXT NOT NULL CHECK (signal_type IN ('HELP','WORK','CIRCLE','BOOKING')),
  raw_text_ciphertext BYTEA NOT NULL,
  raw_text_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN
    ('DRAFT','OPEN','PAUSED','IN_PROGRESS','CLOSED','EXPIRED','CANCELLED','COMPLETED')),
  moderation_status TEXT NOT NULL CHECK (moderation_status IN
    ('ALLOWED','PENDING_REVIEW','BLOCKED','SELF_HARM_ROUTE')),
  matching_mode TEXT NOT NULL CHECK (matching_mode IN ('MATCH','RECRUITMENT')),
  visibility TEXT NOT NULL CHECK (visibility IN ('PUBLIC','LINK_ONLY','PRIVATE')),
  source_language TEXT NOT NULL CHECK (source_language ~ '^[a-z]{2}$'),
  urgency TEXT NOT NULL CHECK (urgency IN ('CRITICAL','HIGH','NORMAL','LOW')),
  requires_physical_presence BOOLEAN NOT NULL DEFAULT false,
  area_hint TEXT, location_city_code TEXT,
  target_is_team BOOLEAN NOT NULL DEFAULT false,
  team_cardinality TEXT NOT NULL CHECK (team_cardinality IN ('1:1','1:N','N:N')),
  headcount_hint INTEGER CHECK (headcount_hint BETWEEN 1 AND 50),
  compensation_is_paid BOOLEAN NOT NULL,
  compensation_amount_minor BIGINT CHECK (compensation_amount_minor IS NULL OR compensation_amount_minor >= 0),
  compensation_currency CHAR(3),
  license_risk_flagged BOOLEAN NOT NULL DEFAULT false,
  license_risk_kind TEXT CHECK (license_risk_kind IN ('DERIVATIVE_IP','TRADEMARK','NONE')),
  license_risk_acknowledged_at TIMESTAMPTZ,
  required_credentials TEXT[] NOT NULL DEFAULT '{}',
  parse_trace_id UUID, parse_schema_version TEXT,
  policy_snapshot JSONB NOT NULL,
  published_at TIMESTAMPTZ, expires_at TIMESTAMPTZ,
  version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK ((compensation_amount_minor IS NULL AND compensation_currency IS NULL)
      OR (compensation_amount_minor IS NOT NULL AND compensation_currency IS NOT NULL)),
  CHECK (compensation_is_paid = true OR compensation_amount_minor IS NULL),
  CHECK ((signal_type='CIRCLE' AND compensation_is_paid=false)
      OR (signal_type IN ('WORK','BOOKING') AND compensation_is_paid=true)
      OR signal_type='HELP')
);

-- ★ 역할은 요청자 폼에서만 온다. source는 단일값이다.
CREATE TABLE signal_roles (
  id UUID PRIMARY KEY,
  signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
  label TEXT NOT NULL CHECK (char_length(label) BETWEEN 1 AND 40),
  normalized_label TEXT NOT NULL,
  headcount INTEGER CHECK (headcount BETWEEN 1 AND 50),
  filled_count INTEGER NOT NULL DEFAULT 0 CHECK (filled_count >= 0),
  source TEXT NOT NULL CHECK (source = 'USER_FORM'),
  form_position INTEGER NOT NULL CHECK (form_position BETWEEN 0 AND 7),
  evidence_span TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (signal_id, form_position)
);

CREATE TABLE signal_skills (
  id UUID PRIMARY KEY,
  signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
  skill_name TEXT NOT NULL CHECK (char_length(skill_name) BETWEEN 1 AND 40),
  origin TEXT NOT NULL CHECK (origin IN ('EXPLICIT','INFERRED','USER_EDITED')),
  evidence_span TEXT,
  confirmation_status TEXT NOT NULL
    CHECK (confirmation_status IN ('NOT_REQUIRED','PENDING','CONFIRMED','REJECTED')),
  confirmed_by UUID REFERENCES users(id) ON DELETE RESTRICT,
  confirmed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK ((origin='EXPLICIT' AND evidence_span IS NOT NULL) OR origin IN ('INFERRED','USER_EDITED')),
  CHECK ((confirmation_status='CONFIRMED' AND confirmed_at IS NOT NULL) OR confirmation_status <> 'CONFIRMED')
);

CREATE TABLE messages (
  id UUID PRIMARY KEY,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE RESTRICT,
  sender_profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  client_message_id TEXT NOT NULL,
  source_text_ciphertext BYTEA NOT NULL,
  source_text_hash TEXT NOT NULL,
  source_lang TEXT NOT NULL CHECK (source_lang ~ '^[a-z]{2}$'),
  delivery_status TEXT NOT NULL CHECK (delivery_status IN
    ('ACCEPTED','DELIVERED','HELD_FOR_REVIEW','NOT_SENT_SAFETY_ROUTE','FAILED')),
  moderation_status TEXT NOT NULL CHECK (moderation_status IN
    ('ALLOWED','PENDING_REVIEW','BLOCKED','SELF_HARM_ROUTE')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (conversation_id, client_message_id)
);

CREATE TABLE message_translations (
  message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  target_lang TEXT NOT NULL CHECK (target_lang ~ '^[a-z]{2}$'),
  translated_ciphertext BYTEA,
  status TEXT NOT NULL CHECK (status IN ('READY','UNSAFE_OR_FAILED','PENDING')),
  ai_trace_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (message_id, target_lang)
);

CREATE TABLE guard_events (
  id UUID PRIMARY KEY,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE RESTRICT,
  sender_profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
  input_hash TEXT NOT NULL,
  risk TEXT NOT NULL, phenomenon TEXT NOT NULL,
  choice TEXT NOT NULL CHECK (choice IN ('ORIGINAL','SUGGESTION')),
  ai_trace_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- ★ guard_events는 trust_events를 만들지 않는다. 트리거·서비스 어디에도 그 경로가 없어야 한다.

CREATE TABLE lens_annotations (
  message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  target_lang TEXT NOT NULL,
  l1_json JSONB NOT NULL,
  l3_json JSONB,
  publishable BOOLEAN NOT NULL DEFAULT false,
  ai_trace_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (message_id, target_lang)
);
-- ★ publishable=false인 L3는 API 응답에 포함하지 않는다.

CREATE TABLE deposit_agreements (
  id UUID PRIMARY KEY,
  collaboration_id UUID NOT NULL UNIQUE REFERENCES collaborations(id) ON DELETE RESTRICT,
  status TEXT NOT NULL CHECK (status IN
    ('PROPOSED','AGREED','FUNDING','LOCKED','REFUND_PENDING','REFUNDED',
     'DISPUTED','FORFEITURE_PENDING','PAID_TO_COUNTERPART','CANCELLED')),
  currency CHAR(3) NOT NULL,
  amount_minor_per_party BIGINT NOT NULL CHECK (amount_minor_per_party > 0),
  cap_policy_version TEXT NOT NULL,
  terms_hash TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- ★ 작업 대금·지분·정산 비율 컬럼은 존재하지 않는다. 추가하면 CI가 막는다.

CREATE TABLE deposit_resolutions (
  id UUID PRIMARY KEY,
  agreement_id UUID NOT NULL REFERENCES deposit_agreements(id) ON DELETE RESTRICT,
  basis TEXT NOT NULL CHECK (basis IN ('MUTUAL_AGREEMENT','OPERATIONS_DECISION')),
  resolved_by_type TEXT NOT NULL CHECK (resolved_by_type IN ('PARTIES','OPERATIONS')),  -- ★ 'AI' 금지
  resolved_by_id UUID,
  outcome TEXT NOT NULL CHECK (outcome IN ('REFUND_ALL','FORFEIT_TO_COUNTERPART','CANCEL_NO_TRANSFER')),
  fault_profile_id UUID REFERENCES profiles(id) ON DELETE RESTRICT,
  beneficiary_profile_ids UUID[] NOT NULL DEFAULT '{}',
  evidence_refs JSONB NOT NULL DEFAULT '[]',
  party_signatures JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 5.4 문화 지식베이스

```sql
CREATE TABLE kb_norms (
  id            TEXT PRIMARY KEY CHECK (id ~ '^[A-Z]{2}-[0-9]{3}$'),   -- "DE-014"
  claim         TEXT NOT NULL,
  scope_locale  TEXT NOT NULL,     -- 언어권 코드. 국가가 아니다.
  scope_context TEXT NOT NULL,     -- '업무 피드백' | '의사 표현' | '호칭·경칭' | '민감 화제' | ...
  sources       JSONB NOT NULL,    -- [{url,title,accessed_at}] 최소 2건
  verified_at   DATE NOT NULL,
  confidence    NUMERIC(3,2) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  disputes      JSONB NOT NULL DEFAULT '[]',
  status        TEXT NOT NULL DEFAULT 'ACTIVE',   -- ACTIVE | RETIRED | CANDIDATE
  embedding     vector(1536) NOT NULL,            -- ★ 1536 고정. 변경은 합의제.
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX kb_norms_hnsw ON kb_norms USING hnsw (embedding vector_cosine_ops);
ALTER TABLE kb_norms ADD CONSTRAINT kb_sources_min
  CHECK (status <> 'ACTIVE' OR jsonb_array_length(sources) >= 2);

CREATE TABLE kb_candidates (
  id UUID PRIMARY KEY,
  term TEXT NOT NULL,
  gloss TEXT,                       -- AI 추정. 확정 아님
  detected_confidence NUMERIC(3,2) NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('PENDING','APPROVED','REJECTED')) DEFAULT 'PENDING',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`scope_locale`은 **국가가 아니라 언어권**이다. `DE`는 독일이 아니라 독일어권 — 오스트리아·스위스 사용자를 국적으로 가르지 않기 위한 데이터 모델 차원의 안전 요건이다.

## 5.5 `matching.v1` — 결정적 기본 정렬

가중치가 미정이므로 가중합을 쓰지 않는다. **hard filter 후 사전식 정렬**이다.

hard filter:
1. 프로필 `ACTIVE`, 자기 요청 프로필 제외
2. PERSON/TEAM 대상 조건 일치 (`target_is_team`)
3. 현장 요청이면 도시 코드 일치 또는 허용 반경 내
4. 정책상 필수 자격 충족
5. 언어 조건·공개 범위 충족

정렬 튜플 (앞에서부터 내림차순, 마지막만 오름차순):

```
( required_skill_exact_match_count,
  requested_role_label_token_match_count,
  professional_or_native_language_match,
  weekly_overlap_minutes,
  verified_relevant_portfolio_count,
  profile_id ASC )
```

- 문화 거리·AI confidence·신뢰 온도·보증금 금액은 튜플에 **없다**.
- availability가 null이면 0분으로 처리하되 후보를 탈락시키지 않는다.
- 직접 검색은 M8 확장어로 계산한 exact term match count를 튜플 맨 앞에 추가한다.
- `rank`는 정렬 결과의 위치일 뿐 AI 출력이 아니다.

## 5.6 미정 정책 격리

| 미정 항목 | 저장·인터페이스 | 현재 기본 동작 |
|---|---|---|
| 모임 매칭 방식 | `signals.matching_mode` | CIRCLE=`RECRUITMENT`, 그 외 `MATCH` |
| 보증금 적용 범위 | `collaborations.deposit_policy_snapshot.applies` | WORK·BOOKING true, HELP·CIRCLE false |
| 자격 검토 방식 | `CredentialVerifier` 포트 | 운영자 수동(시드 스크립트) |
| 과실 판정 주체 | `DepositResolutionPolicy` 포트 | PARTIES·OPERATIONS만, AI 금지, 귀속 플래그 off |
| 매칭 가중치 | `recommendation_runs.policy_version` | `matching.v1` 사전식 |
| 신뢰 계산식 | `TrustProjectionPolicy` 포트 | `trust.v1` 활성 (§5.7) |

## 5.7 `trust.v1` — 결정적 신뢰 온도 (§1.5-A 결론)

```python
# app/policies/trust.py — LLM은 이 파일 근처에도 오지 않는다.
BASE = 36.5
DELTA = {
    "COLLABORATION_COMPLETED": +1.2,
    "NO_SHOW_CONFIRMED":       -2.0,
    "REVIEW_RECEIVED:POSITIVE": +0.3,
    "REVIEW_RECEIVED:NEUTRAL":   0.0,
    "REVIEW_RECEIVED:NEGATIVE": -0.8,
    "DISPUTE_RESOLVED:AT_FAULT": -1.0,
    "DISPUTE_RESOLVED:OTHER":     0.0,
}
FLOOR, CEIL = 30.0, 50.0

def project(events) -> float:
    v = BASE + sum(DELTA[key(e)] for e in events)
    return round(min(CEIL, max(FLOOR, v)), 1)
```

- 입력은 `trust_events` append-only 로그뿐이다. 재계산은 언제나 같은 값을 낸다.
- **`guard_events`(경고 무시)는 입력이 아니다.** 지표 식이 없는데 감점 항목을 먼저 만들 수 없고, 만들면 "차단이 아니라 경고"라는 설계가 무너진다.
- 문화 거리·AI confidence·국적도 입력이 아니다.
- `TRUST_POLICY_VERSION=disabled`면 `status=UNAVAILABLE`, `value=null`, `display_label="평가 데이터 집계 중"`을 반환한다. 프론트는 이 상태를 반드시 지원한다.
- 검산: 완료 1건 = +1.2 → 데모의 `37.3 → 38.5`, `41.2 → 42.4`와 정확히 일치한다.

---

# 6. 백엔드 API

## 6.1 공통 규격

| 항목 | 규격 |
|---|---|
| Base path | `/api/v1` |
| 인증 | `Authorization: Bearer <access_token>` (15분), refresh 30일 회전 |
| 권한 기준 | `user_id`가 아니라 요청의 `acting_profile_id` |
| ID | UUIDv7 문자열 |
| 페이지네이션 | 불투명 cursor, 기본 20 / 최대 100 |
| 동시성 | `version` + `If-Match`; 불일치 409 |
| 멱등성 | 지정 POST에 `Idempotency-Key` 필수, 24시간 유지 |
| 추적 | 응답 `trace_id` 필수 |

성공 봉투 `{"data":…, "meta":{"trace_id","server_time","page?"}}`
오류 봉투 `{"error":{"code","message","details","trace_id"},"meta":{…}}`
사용자에게 보이는 `message`는 안전한 고정 문구다. 스택 트레이스·SQL·공급자 응답 본문을 `details`에 넣지 않는다.

**AI 경로 예외**: `/api/v1/ai/*`는 일반 봉투로 다시 감싸지 않고 §7.2의 E3 봉투를 그대로 반환한다. 이중 래핑은 CI가 막는다.

## 6.2 엔드포인트 목록 (데모 슬라이스)

**인증·계정**

| 메서드 | 경로 |
|---|---|
| POST | `/auth/register` · `/auth/login` · `/auth/refresh` · `/auth/logout` · `/auth/ws-tokens` |
| GET/PATCH/DELETE | `/me` |

**프로필·팀·자격**

| 메서드 | 경로 |
|---|---|
| POST | `/profiles/person` · `/teams` · `/teams/{id}/invitations` · `/team-invitations/{token}/accept` |
| GET/PATCH | `/profiles/{id}` |
| PUT | `/profiles/{id}/skills` · `/profiles/{id}/languages` · `/profiles/{id}/availability` |
| POST | `/uploads` · `/profiles/{id}/credentials` · `/profiles/{id}/portfolios` |
| GET | `/catalog/skills` |

**시그널**

| 메서드 | 경로 |
|---|---|
| POST | `/ai/parse` · `/signals` · `/signals/{id}/publish` · `/signals/{id}/pause` · `/signals/{id}/resume` · `/signals/{id}/close` · `/signals/{id}/cancel` |
| GET/PATCH | `/signals` · `/signals/{id}` |

**검색·추천**

| 메서드 | 경로 |
|---|---|
| POST | `/ai/search-normalize` · `/signals/{id}/recommendation-runs` · `/ai/why` |
| GET | `/search/profiles` · `/signals/{id}/recommendations` |

**지원·협업**

| 메서드 | 경로 |
|---|---|
| POST | `/signals/{id}/applications` · `/applications/{id}/accept` · `/applications/{id}/reject` · `/applications/{id}/withdraw` |
| POST | `/collaborations/{id}/activate` · `/collaborations/{id}/completion-requests` · `/completion-requests/{id}/confirm` · `/completion-requests/{id}/reject` |
| GET | `/signals/{id}/applications` · `/profiles/{id}/applications` · `/collaborations/{id}` |

**대화·AI**

| 메서드 | 경로 |
|---|---|
| POST | `/ai/guard` · `/conversations/{id}/messages` · `/ai/translate` · `/ai/lens` |
| GET | `/conversations/{id}/messages` · `/ai/health` · `/ws` |

**보증금**

| 메서드 | 경로 |
|---|---|
| POST | `/collaborations/{id}/deposit-proposals` · `/deposit-proposals/{id}/agreements` · `/deposit-agreements/{id}/funding-sessions` · `/deposit-agreements/{id}/refunds` · `/webhooks/deposit-provider` · `/ai/deposit-draft` |
| GET | `/deposit-agreements/{id}` |

**평가·신뢰·알림**

| 메서드 | 경로 |
|---|---|
| POST | `/collaborations/{id}/reviews` · `/notifications/{id}/read` |
| GET | `/profiles/{id}/reviews` · `/profiles/{id}/trust` · `/notifications` |

## 6.3 상태 머신

**시그널**

```mermaid
%%{init: {"state": {"nodeSpacing": 50, "rankSpacing": 60, "useMaxWidth": true}}}%%
stateDiagram-v2
    direction TB
    [*] --> DRAFT
    DRAFT --> OPEN : publish
    DRAFT --> CANCELLED : cancel
    OPEN --> PAUSED : pause
    PAUSED --> OPEN : resume
    OPEN --> IN_PROGRESS : activate
    OPEN --> CLOSED : close
    OPEN --> EXPIRED : expire
    OPEN --> CANCELLED : cancel
    IN_PROGRESS --> COMPLETED : complete
    IN_PROGRESS --> CANCELLED : cancel
```

| 전이 | 조건 |
|---|---|
| `publish` | §6.4 발행 게이트 9종 전부 통과 |
| `activate` | 지원 수락으로 협업이 `ACTIVE`가 됨 |
| `close` | 모집 정원 도달 또는 요청자가 직접 마감 |
| `expire` | `expires_at` 도달 |
| `cancel` (OPEN) | 활성 협업이 없을 때만 |
| `cancel` (IN_PROGRESS) | 결의로 취소가 허용된 경우만 |

역할 `headcount=null`이고 전체 `headcount_hint=null`이면 미정원으로 취급한다. **서버가 인원을 추정하지 않으며**, 이때는 자동 마감 없이 요청자가 직접 닫는다.

**지원 · 협업 · 보증금**

```
지원:   PENDING → ACCEPTED → COLLABORATION_CREATED | REJECTED | WITHDRAWN
협업:   AGREEMENT_PENDING → (보증금 적용 시) DEPOSIT_PENDING → ACTIVE
        ACTIVE → COMPLETION_PENDING → COMPLETED | (반려 시) ACTIVE
        ACTIVE|DEPOSIT_PENDING → DISPUTED → ACTIVE | CANCELLED
보증금: PROPOSED → AGREED → FUNDING → LOCKED → REFUND_PENDING → REFUNDED
        LOCKED → DISPUTED → FORFEITURE_PENDING → PAID_TO_COUNTERPART (플래그 off, 데모 미사용)
```

## 6.4 발행 게이트 — `DRAFT → OPEN`

아래를 **모두** 만족해야 한다.

1. `raw_text` 1~4,000자
2. 요청자 프로필 `ACTIVE`
3. `roles_requested`가 최초 역할 폼과 **정확히 같고**, 모든 row의 `source='USER_FORM'`
4. 값이 있는 `origin=INFERRED` 항목을 사용자가 확인하거나 수정함
5. `signal_type`과 `compensation.is_paid` 기본 규칙을 사용자가 확인함
6. `license_risk.flagged=true`이면 파생 IP 주의 확인 시각 존재 (확인은 허가 판정이 아니다)
7. 고위험 자격 탐지 시 결정적 고지문 확인 시각 존재
8. 모더레이션 상태 `ALLOWED`
9. PII lint 통과 (정밀 좌표·연락처·자격증 원본이 원문에 없음)

`duration.weeks=null`, `compensation.amount_minor=null`은 **결측이지 추론값이 아니다.** null 자체는 확인 대상이 아니며 서버가 숫자를 채워 넣지 않는다.

## 6.5 역할 불변식의 서버 검증 (이 제품의 핵심 계약)

```text
normalize(label) = Unicode NFKC → 양끝 공백 제거 → 연속 공백 1개
role_key = (form_position, normalize(label), headcount)

multiset(request.roles_form.role_key)
  == multiset(ai.data.roles_requested.role_key)
  == multiset(signal_roles.role_key)
```

하나라도 다르면 **AI 결과를 폐기하고** 결정적 폴백의 역할 배열(= `roles_form` 원본 복사)을 쓴다. 프론트가 파싱 뒤 역할을 바꾸면 새 파싱 실행을 만들거나 AI 결과 없이 draft를 수정해야 한다.

## 6.6 메시지 발신 오케스트레이션

```mermaid
%%{init: {"sequence": {"useMaxWidth": true, "wrap": false, "messageAlign": "center"}}}%%
sequenceDiagram
    autonumber
    participant FE as 프론트
    participant BE as 백엔드
    participant MOD as 모더레이션
    participant AI as AI 레이어
    FE->>BE: 메시지 발신
    BE->>BE: 멤버십 · 멱등성 · 가드 해시
    BE->>MOD: 원문 검사
    alt 자해 신호
        MOD-->>BE: SELF_HARM_ROUTE
        BE-->>FE: 위기 안내 · AI 미호출
    else 검토 필요
        MOD-->>BE: PENDING_REVIEW
        BE-->>FE: 접수됨 · 미전달
    else 허용
        BE->>AI: 번역 요청
        AI-->>BE: 번역 또는 실패
        BE->>BE: 숫자 · 길이 · 의도 재검증
        BE-->>FE: 202 접수 + 번역 상태
        BE->>AI: 렌즈 요청 · 비동기
        AI-->>BE: 직역 + 게이트 통과분
        BE-->>FE: 주석 준비됨
    end
```

번역 실패 시 메시지는 **원문으로 발신**하고 `translation_status=UNSAFE_OR_FAILED`, `display_chip=TRANSLATION_REVIEW_REQUIRED`를 내려준다. 메시지를 조용히 드롭하지 않는다.

## 6.7 오류 코드 (제품 영역)

`AUTH_INVALID_CREDENTIALS`(401) · `AUTH_SESSION_REUSED`(401) · `ACTING_PROFILE_FORBIDDEN`(403) · `PROFILE_NOT_ACTIVE`(422) · `TEAM_OWNER_REQUIRED`(403) · `TEAM_LAST_OWNER`(409) · `CREDENTIAL_REVIEW_REQUIRED`(422) · `UPLOAD_NOT_SCANNED`(409) · `SIGNAL_INVALID_TRANSITION`(409) · `SIGNAL_VERSION_CONFLICT`(409) · `SIGNAL_ROLE_SOURCE_INVALID`(422) · `SIGNAL_ROLE_MISMATCH`(422) · `SIGNAL_INFERENCE_CONFIRMATION_REQUIRED`(422) · `SIGNAL_LICENSE_ACK_REQUIRED`(422) · `SIGNAL_HIGH_RISK_DISCLAIMER_REQUIRED`(422) · `SIGNAL_MODERATION_REVIEW_REQUIRED`(422) · `SIGNAL_CAPACITY_EXCEEDED`(409) · `APPLICATION_DUPLICATE`(409) · `APPLICATION_CREDENTIAL_REQUIRED`(422) · `COLLABORATION_INVALID_TRANSITION`(409) · `CONVERSATION_ACCESS_DENIED`(403) · `MESSAGE_GUARD_STALE`(409) · `DEPOSIT_NOT_APPLICABLE`(409) · `DEPOSIT_CAP_EXCEEDED`(422) · `DEPOSIT_TERMS_CHANGED`(409) · `DEPOSIT_PARTIES_NOT_AGREED`(409) · `DEPOSIT_NOT_LOCKED`(409) · `DEPOSIT_RESOLUTION_REQUIRED`(409) · `DEPOSIT_PROVIDER_EVENT_INVALID`(400) · `REVIEW_NOT_ALLOWED`(409) · `IDEMPOTENCY_KEY_REQUIRED`(400) · `IDEMPOTENCY_KEY_REUSED`(409) · `RATE_LIMITED`(429)

**503은 DB/Redis 장애에만 쓴다. AI 모델 장애에는 절대 쓰지 않는다.**

## 6.8 Rate limit

로그인 IP당 10회/10분 · 일반 읽기 300/분 · 일반 쓰기 60/분 · `/ai/guard` 30/분(동일 해시 60초 캐시) · 그 외 `/ai/*` 20/분 · 검색 60/분 · 메시지 대화당 30/분 · 업로드 URL 20/시간.

---

# 7. AI 레이어 (E3 · `pangaea_ai`)

> 이 절의 스키마·프롬프트·게이트는 `AI레이어_개발명세서_v2.0.md`가 정본이다. 수정하지 말고 그대로 구현한다.

## 7.1 모듈 8종과 티어 배치

| 모듈 | 엔드포인트 | 모델 | effort | p95 상한 | 폴백 |
|---|---|---|---|---|---|
| M1 요청 파서 | `POST /ai/parse` | luna | none | 2.0s | 키워드 사전 + 정규식. **역할은 폼 입력이라 무손실** |
| M2 렌즈 L1 (직역) | `POST /ai/lens` | luna | none | 1.0s | 원문 그대로, 주석 없음 |
| M2 렌즈 L2·L3 (뉘앙스·의도) | 〃 | terra | low | 2.5s | **없음 — 주석을 달지 않는다** |
| M3 발신 가드 | `POST /ai/guard` | luna | none | 1.2s | 금기 표현 사전(≈80구 + 호칭 ≈30구) 정규식, 수정안 없이 경고만 |
| M4 발신 번역 | `POST /ai/translate` | luna | none | 1.5s | **없음 — 원문 발신 + 「번역 확인 필요」 칩** |
| M5 RAG·근거 인용 | (내부) | embed | — | — | 사전 동의어 |
| M6 추천 이유 | `POST /ai/why` | luna | none | 1.5s | 고정 슬롯 템플릿 |
| M7 보증금 문구 | `POST /ai/deposit-draft` | terra | low | 3.0s | 결정적 조항 템플릿 |
| M8 검색 정규화 | `POST /ai/search-normalize` | luna | none | 0.8s | 원 질의어 + 사전 동의어 |
| 안전 검사 | (전처리) | omni-moderation | — | — | — |

**상시 경로에 고티어는 없다.** `sol`은 평가셋 LLM-judge 전용이며, 런타임 코드가 `MODELS["judge"]`를 참조하면 CI 린트가 잡는다.

**모델 ID는 `pangaea_ai/config.py` 한 곳에만 존재한다.**

```python
MODELS = {
    "low":   os.getenv("PANGAEA_MODEL_LOW",   "gpt-5.6-luna"),
    "mid":   os.getenv("PANGAEA_MODEL_MID",   "gpt-5.6-terra"),
    "judge": os.getenv("PANGAEA_MODEL_JUDGE", "gpt-5.6-sol"),    # 평가 전용
    "embed": os.getenv("PANGAEA_MODEL_EMBED", "text-embedding-3-large"),
    "mod":   os.getenv("PANGAEA_MODEL_MOD",   "omni-moderation-latest"),
}
EMBED_DIMENSIONS = 1536   # 계약. 변경은 Alembic PR + 합의제.
```

부팅 시 `GET /v1/models`로 등록 ID 실재를 검증하고, 없으면 **기동을 실패시킨다**(`AI-007`). 오타난 모델 ID로 시연장에서 404를 맞는 사고를 막는 장치다. 단 `AI_MODE=stub`에서는 이 검사를 건너뛴다.

## 7.2 공통 응답 봉투

```jsonc
{
  "ok": true,
  "data": { /* 스키마 검증 통과분 또는 결정적 폴백 결과 */ },
  "degraded": false,
  "degrade_reason": null,   // SCHEMA_VIOLATION | TIMEOUT | TRUNCATED | NO_EVIDENCE
                            // | BUDGET | MODERATION | REFUSAL | TRANSLATION_UNSAFE
  "meta": {
    "module": "parse", "model": "gpt-5.6-luna", "mode": "live",
    "latency_ms": 1180,
    "tokens": {"input":1204,"cached":1024,"cache_write":0,"output":342,"reasoning":0},
    "cost_krw": 0.67, "trace_id": "01J…", "schema_version": "parse.v2"
  }
}
```

- `ok:false`여도 `data`는 **null이 아니라 결정적 폴백 결과**다. 화면이 비는 상황을 만들지 않는다.
- `degraded:true`면 프론트는 주황 「간이 모드」 칩을 띄운다.
- 모델 원문이 이 봉투 밖으로 나가는 경로는 없다.

## 7.3 표준 호출 규격

```python
resp = client.responses.create(
    model=MODELS["low"],
    instructions=SYSTEM_PROMPT_PARSE,                 # 정적 — 캐시 프리픽스
    input=[{"role":"user","content":user_text}],      # 동적 — 뒤에
    text={"format":{"type":"json_schema","name":"signal_parse",
                    "schema":SIGNAL_PARSE_SCHEMA,"strict":True}},
    reasoning={"effort":"none"},
    max_output_tokens=800,
    prompt_cache_key="pangaea-parse-v2",
    timeout=6.0,
)
```

strict 모드 규칙: 모든 필드 `required`(선택값은 `anyOf: [{…},{"type":"null"}]`), 모든 object에 `additionalProperties:false`, **단일값 enum 유효**, 루트 레벨 `anyOf`·`allOf`·`if/then/else`·`patternProperties` 사용 불가.

응답은 파싱 **전에** 3단 검사를 통과해야 한다.

```python
if any(c.type == "refusal" for c in item.content):        return fallback("REFUSAL")
if resp.status == "incomplete":                            return fallback("TRUNCATED")
try:    data = SignalParse.model_validate_json(resp.output_text)
except ValidationError:                                    return repair_or_fallback("SCHEMA_VIOLATION")
```

③의 Pydantic 재검증이 **"스키마 불통과 응답은 폐기 후 폴백"의 실제 구현 지점**이다. 서버 응답을 믿지 않는다.

**재시도**: 429/5xx는 지수 백오프 2회(0.5s, 1.5s + 지터). 스키마 위반은 수리 프롬프트로 **1회만**. refusal은 재시도 금지. 승급은 모듈당 요청당 최대 1회, 재귀 승급 금지.

**캐시**: 정적(시스템 프롬프트·few-shot) 앞, 동적(사용자 입력·KB 결과·타임스탬프) 뒤. 시스템 프롬프트에 타임스탬프·UUID를 절대 넣지 않는다(1바이트만 달라도 미스). 프롬프트를 고치면 `prompt_cache_key` 버전을 올린다.

## 7.4 M1 요청 파서 — 스키마 (`parse.v2`)

```jsonc
{
  "type":"object","additionalProperties":false,
  "required":["signal_type","urgency","skills","roles_requested","duration","team_shape",
              "compensation","deliverables","location_requirement","license_risk",
              "required_credentials","source_language","confidence","unmapped_spans"],
  "properties":{
    "signal_type":{"type":"string","enum":["HELP","WORK","CIRCLE","BOOKING"]},
    "urgency":{"type":"string","enum":["CRITICAL","HIGH","NORMAL","LOW"]},

    // ★ AI는 역할을 설계하지 않는다. origin이 단일값이라 INFERRED가 표현 불가능하다.
    "roles_requested":{"type":"array","maxItems":8,
      "items":{"type":"object","additionalProperties":false,
        "required":["label","origin","evidence_span","headcount"],
        "properties":{
          "label":{"type":"string","maxLength":40},
          "origin":{"type":"string","enum":["EXPLICIT"]},
          "evidence_span":{"type":"string"},
          "headcount":{"anyOf":[{"type":"integer","minimum":1,"maximum":50},{"type":"null"}]}}}},

    "skills":{"type":"array","maxItems":8,
      "items":{"type":"object","additionalProperties":false,
        "required":["name","origin","evidence_span","importance"],
        "properties":{
          "name":{"type":"string","maxLength":40},
          "origin":{"type":"string","enum":["EXPLICIT","INFERRED"]},
          "evidence_span":{"type":"string"},
          "importance":{"type":"number","minimum":0,"maximum":1}}}},

    "duration":{"type":"object","additionalProperties":false,
      "required":["weeks","origin","evidence_span"],
      "properties":{
        "weeks":{"anyOf":[{"type":"integer","minimum":1,"maximum":104},{"type":"null"}]},
        "origin":{"type":"string","enum":["EXPLICIT","INFERRED","DEFAULT"]},
        "evidence_span":{"anyOf":[{"type":"string"},{"type":"null"}]}}},

    "team_shape":{"type":"object","additionalProperties":false,
      "required":["cardinality","headcount_hint","target_is_team"],
      "properties":{
        "cardinality":{"type":"string","enum":["1:1","1:N","N:N"]},
        "headcount_hint":{"anyOf":[{"type":"integer","minimum":1,"maximum":50},{"type":"null"}]},
        "target_is_team":{"type":"boolean"}}},

    // ★ 앱은 이 금액의 결제에 관여하지 않는다. 매칭 조건 표시용 참고값.
    "compensation":{"type":"object","additionalProperties":false,
      "required":["is_paid","amount_krw","currency","origin","evidence_span"],
      "properties":{
        "is_paid":{"type":"boolean"},
        "amount_krw":{"anyOf":[{"type":"integer","minimum":0},{"type":"null"}]},
        "currency":{"type":"string","enum":["KRW","USD","JPY","EUR","NONE"]},
        "origin":{"type":"string","enum":["EXPLICIT","INFERRED","NONE"]},
        "evidence_span":{"anyOf":[{"type":"string"},{"type":"null"}]}}},

    "deliverables":{"type":"array","maxItems":8,
      "items":{"type":"object","additionalProperties":false,
        "required":["name","evidence_span"],
        "properties":{"name":{"type":"string","maxLength":60},
                      "evidence_span":{"type":"string"}}}},

    "location_requirement":{"type":"object","additionalProperties":false,
      "required":["requires_physical_presence","area_hint","origin"],
      "properties":{
        "requires_physical_presence":{"type":"boolean"},
        "area_hint":{"anyOf":[{"type":"string","maxLength":60},{"type":"null"}]},
        "origin":{"type":"string","enum":["EXPLICIT","INFERRED","NONE"]}}},

    "license_risk":{"type":"object","additionalProperties":false,
      "required":["flagged","kind","rationale"],
      "properties":{
        "flagged":{"type":"boolean"},
        "kind":{"type":"string","enum":["DERIVATIVE_IP","TRADEMARK","NONE"]},
        "rationale":{"anyOf":[{"type":"string","maxLength":200},{"type":"null"}]}}},

    "required_credentials":{"type":"array","maxItems":5,
      "items":{"type":"string","enum":["MEDICAL_LICENSE","LEGAL_LICENSE","INTERPRETER","DRIVER_LICENSE","NONE"]}},

    "source_language":{"type":"string","pattern":"^[a-z]{2}$"},
    "confidence":{"type":"number","minimum":0,"maximum":1},
    "unmapped_spans":{"type":"array","maxItems":10,"items":{"type":"string"}}
  }
}
```

**이 스키마에 없는 것이 핵심이다**: AI 설계 역할(`roles[]`), `role_weight`·`split_ratio`, `deposit_amount`, `match_score`·`rank`·`indicator`.

`origin`의 의미: `EXPLICIT`=원문에 있음(그대로 태그 표시) · `INFERRED`=AI 추론(**점선 테두리 + 「추정」 배지**, 사용자가 한 번 확인해야 발행 가능) · `DEFAULT`=규칙 기본값.

시스템 프롬프트 핵심 조항(그대로 사용):

```
[역할 경계 — 가장 중요]
- 너는 추출만 한다. 점수·순위·지표·보증금·정산을 만들지 않는다. 스키마에 그런 필드는 없다.
- **역할(roles_requested)은 절대 만들지 않는다.** 요청자가 [요청자 명시 역할] 블록에
  적어 준 항목만 그대로 옮긴다. 블록이 비어 있으면 빈 배열이다.
  요청 내용상 다른 역할이 필요해 보여도 추가하지 않는다. 그건 네 일이 아니다.
- 원문에 없는 사실을 EXPLICIT으로 표시하지 않는다. 추론했으면 반드시 origin="INFERRED"다.
- duration·compensation에 원문 수치가 없으면 null로 두고 숫자를 지어내지 않는다.
  ※ 스킬은 추론해도 되지만 역할은 안 된다. 스킬은 매칭 조건이고 역할은 팀 설계다.
```

E2 동적 입력 형식:

```text
[자연어 요청]
에반게리온 팬게임 같이 만들 사람 찾아요. 6주 정도 보고 있고, …

[요청자 명시 역할]
0 | 기획 · 디렉팅 | 1명
1 | 클라이언트 개발 | 1명
2 | 캐릭터 아트 | 1명
```

## 7.5 M2 컬처 렌즈 — 3층과 발행 게이트

| 층 | 하는 일 | 화면 |
|---|---|---|
| L1 직역 | 원문을 문자 그대로 옮김 | **언제나 표시** — 「원문 —」 |
| L2 뉘앙스 | 직설도·정중도·완곡 표지·발화 행위 태깅 | 화면 비노출, L3 입력 |
| L3 의도 | KB 근거를 인용한 **경향** 주석 | **근거가 있을 때만 표시** |

이 비대칭이 ADR-005의 전부다.

```python
def may_publish_l3(l3, kb) -> bool:
    if not l3.applies:                          return False
    if not l3.kb_ids:                           return False   # ① 근거 없으면 미표시
    if any(k not in kb for k in l3.kb_ids):     return False   # ② 존재하지 않는 KB ID = 환각
    eff = min(effective_confidence(kb[k]) for k in l3.kb_ids)
    if eff < AI_L3_MIN_CONFIDENCE:              return False   # ③ 기본 0.50
    if not stereotype_lint(l3.annotation):      return False   # ④ 단정 표현 금지
    return True
```

**② 가 조용한 환각을 잡는 지점이다.** 모델이 `DE-099` 같은 그럴듯한 ID를 지어내도 실재 조회에서 걸린다.

**④ 단정 표현 린트**

```python
BANNED = [r"(모든|전부|항상|원래|다)\s*\S*\s*(사람들|인들)은",
          r"\S+인은\s+\S+하다$",
          r"(절대|반드시)\s+\S+(한다|합니다)"]
REQUIRED_ANY = ["경우가 많","경향이 있","편입니다","~하는 편","일반적으로","자주","많습니다"]
```

경향 표지가 하나도 없으면 탈락. 목업의 주석들이 「~인 편이에요」·「~인 경우가 있어요」로 끝나는 것은 우연이 아니라 이 게이트의 산물이어야 한다.

**확신도 감쇠 (결정적 코드)**

```python
HALFLIFE_DAYS, DISPUTE_PENALTY, CONF_FLOOR = 365, 0.05, 0.30

def effective_confidence(rec, today):
    decayed = rec.confidence * (0.5 ** ((today - rec.verified_at).days / HALFLIFE_DAYS))
    return max(CONF_FLOOR, round(decayed - DISPUTE_PENALTY * len(rec.disputes), 2))
```

검산: `DE-014` (base 0.74, verified 2026-08-05, 7일 경과, 이의 3건) → `0.74 × 0.5^(7/365) = 0.7302 − 0.15 = 0.58`.
화면 3단 표시: **강 ≥0.75 / 보통 0.65–0.75 / 참고 0.50–0.65**. KB 시트에는 base와 유효 확신도를 **둘 다** 적는다.

**신조어**: `confidence < 0.5`면 「이 표현은 최근 생긴 말일 수 있어요」 중립 안내만. 뜻을 지어내 설명하지 않는다. 탐지분은 `kb_candidates`에 적재한다.

## 7.6 M3 발신 전 가드

```jsonc
{
  "type":"object","additionalProperties":false,
  "required":["risk","phenomenon","reader_reading","suggestion","kb_ids","confidence","direction"],
  "properties":{
    "risk":{"type":"string","enum":["NONE","LOW","MEDIUM","HIGH"]},
    "phenomenon":{"type":"string","enum":[
      "EUPHEMISTIC_REFUSAL","OVERLY_DIRECT","VAGUE_DEADLINE","HONORIFIC_MISMATCH",
      "UNTRANSLATABLE_IDIOM","IMPLIED_OBLIGATION",
      "TABOO_ADDRESS","TABOO_TOPIC","NONE"]},
    "reader_reading":{"anyOf":[{"type":"string","maxLength":150},{"type":"null"}]},
    "suggestion":{"anyOf":[{"type":"string","maxLength":250},{"type":"null"}]},
    "kb_ids":{"type":"array","maxItems":3,"items":{"type":"string","pattern":"^[A-Z]{2}-[0-9]{3}$"}},
    "confidence":{"type":"number","minimum":0,"maximum":1},
    "direction":{"type":"string","pattern":"^[a-z]{2}->[a-z]{2}$"}
  }
}
```

**표시 조건**

```
표시 = ( risk ∈ {MEDIUM, HIGH}
       ∨ (risk = LOW ∧ phenomenon ∈ {TABOO_ADDRESS, TABOO_TOPIC}) )   ← 실례는 작아도 알린다
     ∧ confidence ≥ 0.70
     ∧ (kb_ids ≠ ∅ ∧ 전부 실재)
     ∧ suggestion ≠ null
```

대안 없는 경고는 사용자를 얼어붙게 만들 뿐이므로 `suggestion`을 필수 조건에 넣는다.

**수정안 생성 규칙**

```
[허용] 모호한 기한 → 구체적 기한 명시 / 완곡한 보류 → 보류임을 분명히
[허용] 직설적 지적 → 사안 중심임을 명시하는 한 문장 추가
[허용] 실례가 되는 호칭 → 중립 호칭으로 교체
[금지] 거절 → 수락, 수락 → 거절
[금지] 없던 약속·기한·수치를 만들어 넣기
[금지] 원문에 없는 사과·감정 표현 추가
[금지] 화제 자체를 삭제 — 금기 화제는 "표현을 고르라"고 알릴 뿐 검열하지 않는다
```

수정안의 날짜는 **AI가 지어내지 않는다.** 협업 컨텍스트(겹침 창·마일스톤)에서 슬롯으로 주입하거나, 슬롯을 비워 `[기한]까지`로 두고 사용자가 채우게 한다.

**사전 계산**: 입력이 400ms 멈추면 `/ai/guard`를 미리 호출해 세션에 캐싱한다. 사용자가 보내기를 누르는 순간엔 네트워크를 타지 않고 즉시 뜬다.

**HIGH여도 발신 버튼은 살아 있다.** 모달이 아니라 인라인 패널이고, 「그대로 보내기」가 항상 왼쪽에 있다.
발신 후 배지: 수정안 적용 → 청록 「보내기 전 확인 통과」 / 그대로 발신 → 주황 「확인 없이 보냄 — 기록됨」. **이 기록은 신뢰 지표에 반영하지 않는다.**

## 7.7 M4 발신 번역과 결정적 검사

```jsonc
{
  "type":"object","additionalProperties":false,
  "required":["translated","target_lang","intent_preserved","additions_made",
              "untranslatable","register","confidence"],
  "properties":{
    "translated":{"type":"string","maxLength":1200},
    "target_lang":{"type":"string","pattern":"^[a-z]{2}$"},
    "intent_preserved":{"type":"boolean"},
    "additions_made":{"type":"boolean"},
    "untranslatable":{"type":"array","maxItems":5,
      "items":{"type":"object","additionalProperties":false,
        "required":["term","handling","gloss"],
        "properties":{"term":{"type":"string","maxLength":40},
                      "handling":{"type":"string","enum":["KEEP_ORIGINAL","GLOSS","OMIT_SAFE"]},
                      "gloss":{"anyOf":[{"type":"string","maxLength":120},{"type":"null"}]}}}},
    "register":{"type":"string","enum":["CASUAL","NEUTRAL","POLITE","FORMAL"]},
    "confidence":{"type":"number","minimum":0,"maximum":1}
  }
}
```

자기 신고(`intent_preserved`)를 게이트로 쓰지 않는다. **기계로 검증 가능한 것은 기계가 검증한다.**

```python
NUM = re.compile(r"\d+(?:[.,]\d+)*")

def translation_safe(src, out):
    if Counter(NUM.findall(src)) != Counter(NUM.findall(out.translated)):
        return False, "NUMERAL_MISMATCH"          # ① 숫자 다중집합이 정확히 같아야 한다
    if len(out.translated) > len(src) * AI_TRANSLATE_MAX_EXPANSION + 40:
        return False, "LENGTH_BLOWUP"             # ②
    if out.additions_made or not out.intent_preserved:
        return False, "SELF_REPORTED_UNSAFE"      # ③
    if guard_speech_act and back_speech_act(out) != guard_speech_act:
        return False, "SPEECH_ACT_DRIFT"          # ④
    return True, ""
```

**①이 핵심이다.** "금요일까지"가 "다음 주까지"로, "3주"가 "3 months"로 바뀌는 사고는 번역에서 흔하고 협업 맥락에서 치명적이다.

실패 처리: terra로 1회 재번역 → 여전히 실패면 `TRANSLATION_UNSAFE` → **원문 그대로 발신 + 「번역 확인 필요」 칩 + 원문 보기 토글**. 번역을 못 했다고 발신을 막지 않고, 틀린 번역을 조용히 내보내지도 않는다.

## 7.8 M5 RAG 검색 파이프라인

```
① 하드 필터(SQL)  status='ACTIVE' ∧ scope_locale = 상대 언어권
② 벡터 검색(HNSW) L1 직역 임베딩 vs claim 임베딩, top-k=8
③ 컨텍스트 필터   scope_context 일치 (렌즈: 업무 피드백/일정 조율/거절 · 가드: 호칭·경칭/민감 화제)
④ 확신도 필터     effective_confidence ≥ 0.50
⑤ 재순위          cosine × effective_confidence → top-3만 프롬프트 주입
```

⑤가 중요하다. 유사도만으로 자르면 오래되고 이의가 많은 레코드가 상위에 남는다.

임베딩: `text-embedding-3-large` + `dimensions=1536`, **축약 후 재정규화**. 임베딩 텍스트는 `f"{scope_locale} | {scope_context} | {claim}"` — claim만 넣으면 언어권이 다른 유사 규범이 섞인다.

프롬프트 주입 형식(모델이 ID를 지어낼 여지를 없앤다):

```
[인용 가능한 근거 — 이 목록 밖의 ID를 쓰면 출력은 폐기된다]
- DE-014 | de | 업무 피드백 | 직설적 지적은 사안 중심인 경우가 많다 | eff_conf 0.58
- JP-007 | ja | 의사 표현   | 정중한 보류가 거절로 기능하는 경우가 많다 | eff_conf 0.71
근거가 부족하면 applies=false, kb_ids=[]로 출력하라. 추측으로 채우지 마라.
```

## 7.9 M6 추천 이유 — AI에게 숫자를 주지 않는다

```
E2 → AI : available_slots(이름만) + 공개 가능한 facts(문장)
            ["skill","years","overlap_hours","verified_count","portfolio_match","city","lang"]
AI  → E2 : "{{skill}} 경력 {{years}}년이고, 포트폴리오가 요구 스킬과 {{portfolio_match}}로 겹칩니다."
            slots_used: [...]
E2 코드  : 결정적 치환 → "Unity 경력 8년이고, … 코사인 0.95로 겹칩니다."
```

검증 4종(전부 결정적): ① 템플릿에 `{{}}` 밖 아라비아 숫자가 있으면 폐기 ② `slots_used ⊆ available_slots` ③ 치환 후 미치환 `{{}}` 잔존 시 폐기 ④ 한국어 조사는 `{{skill:이/가}}` 표기로 받고 받침 판정은 결정적 처리기가 한다.

**`{{indicator}}`·`{{score}}`·`{{rank}}` 슬롯은 제공하지 않는다.** 슬롯이 없으면 AI는 지표를 언급할 문법적 수단이 없다. 나중에 식이 확정되면 슬롯 하나를 추가하는 것으로 끝난다 — 프롬프트도 스키마도 고치지 않는다.

## 7.10 M7 보증금 문구 / M8 검색 정규화

**M7** — 금액·상한·과실은 슬롯 이름으로만 등장한다. `clause_key` enum은 규칙 엔진 출력과 1:1(`DEPOSIT`·`DERIVATIVE_IP`·`ASYNC_COLLAB`·`CREDENTIAL`·`DELIVERABLE_HASH`·`DISSOLUTION`). 조항 삽입 여부가 모델 출력에 좌우되면 법적 리스크다.
필수 주의 문구: **「보증금은 작업 대금이 아닙니다. 대금 지급 방법은 당사자끼리 따로 정해야 합니다.」**

**M8** — 출력에 `boost`·`weight`·`sort_order`·`results` 필드가 없다. AI는 질의어를 넓히기만 한다: `밴드 → {band, バンド, Band}`. 순위는 서버가 정한다.

## 7.11 폴백 체인 · 예산 · 모드

```
호출
 ├─ 모더레이션 차단 ──▶ MODERATION       → 전용 안내 (자해 계열은 AI 미호출)
 ├─ 타임아웃 ─────────▶ TIMEOUT          → 결정적 폴백
 ├─ refusal ─────────▶ REFUSAL          → 결정적 폴백 + warn
 ├─ incomplete ──────▶ TRUNCATED        → 결정적 폴백
 ├─ 스키마 위반 ─수리1회┬ 성공 → 정상(meta.repaired=true)
 │                      └ 실패 → SCHEMA_VIOLATION → 결정적 폴백
 ├─ 번역 검사 실패 ─terra1회┬ 성공 → 정상
 │                          └ 실패 → TRANSLATION_UNSAFE → 원문 병기 발신
 ├─ 게이트 탈락 ──────▶ NO_EVIDENCE      → 주석·가드 미표시 (에러가 아니다)
 └─ 예산 초과 ────────▶ BUDGET           → 티어 강등 → replay
```

`NO_EVIDENCE`는 **에러가 아니라 의도된 동작**이다. info 레벨로만 남기고 "게이트 발동률" 지표로 노출한다 — 심사에서 보여줄 숫자다.

**예산 강등**: 80% 소진 → 렌즈 L2·L3 최소 출력, M7이 luna. 90% → 렌즈가 luna, 주석 게이트 임계 0.70 상향. 100% → `AI_MODE=replay` 전환, 전 모듈 결정적 폴백. **서비스는 계속 돈다.**

**3중 모드**

```
AI_MODE=live     실제 OpenAI 호출
AI_MODE=replay   입력 해시로 fixtures/ai/*.json 조회, 없으면 stub
AI_MODE=stub     네트워크 0, 결정적 규칙 기반 출력만
```

캐시 키 `sha256(module + schema_version + prompt_version + normalized_input)`. **CI 기본값은 stub이며, 키 없이 전부 통과해야 한다.** 시연은 replay 고정.

## 7.12 AI 에러 코드

| 코드 | 의미 | HTTP |
|---|---|---|
| `AI-001` | 스키마 위반(수리 실패) | 200 + degraded |
| `AI-002` | 타임아웃 | 200 + degraded |
| `AI-003` | 모델 거부 | 200 + degraded |
| `AI-004` | 근거 없음 → 주석 미표시 | 200, degraded=false (정상) |
| `AI-005` | 예산 초과 → replay | 200 + degraded |
| `AI-006` | 모더레이션 차단 | 200 + 전용 안내 |
| `AI-007` | 모델 ID 미등록 | 기동 실패 |
| `AI-008` | 번역 의도·숫자 검사 실패 | 200 + degraded |

**AI 레이어는 5xx를 반환하지 않는다.** 화면이 비는 것보다 간이 모드가 낫다.

## 7.13 E2⇄E3 전달 허용 목록

| 경로 | 전달함 | 전달 금지 |
|---|---|---|
| `/ai/parse` | 자연어 요청, 정확한 역할 폼 블록 | 사용자 ID, 연락처, 추천 점수, 보증금 |
| `/ai/lens` | 메시지 원문, source/target lang, 상황 맥락, top-3 KB | 실명, 국적 판정, 정밀 위치, 신뢰값 |
| `/ai/guard` | 최종 후보 문장, direction, 상대 언어권, 맥락, KB | 사용자 평점, 제재 이력, 금액·점수 |
| `/ai/translate` | 확정 발신 문장, lang, guard speech act | 연락처, 평가 값 |
| `/ai/why` | 슬롯 **이름**, 공개 가능한 facts, language | 슬롯 실제 값, score, rank, indicator |
| `/ai/deposit-draft` | `deposit_applies`, clause keys, 슬롯 이름 | 실제 금액·상한·과실 당사자·정산 비율 |
| `/ai/search-normalize` | 검색 문자열, query language | 검색 결과, boost, weight, rank |

프롬프트 인젝션은 데이터로만 취급한다. 동적 입력은 명확한 delimiter와 필드 라벨로 감싼다. URL은 보존 대상으로만 전달하며 AI가 fetch하지 않는다.

---

# 8. 실시간과 이벤트

**WebSocket**: `GET /api/v1/ws?ws_token=…`. access token을 쿼리에 넣지 않고 `POST /auth/ws-tokens`로 60초 1회용 토큰을 발급한다.

지원 이벤트: `signal.application.created.v1` · `signal.application.updated.v1` · `collaboration.updated.v1` · `message.created.v1` · `message.translation.ready.v1` · `message.lens.ready.v1` · `message.moderation.updated.v1` · `deposit.updated.v1` · `notification.created.v1`.

클라이언트는 모르는 이벤트를 무시하고, 재연결 후 `last_event_id` 이후를 요청한다. 보존 기간을 넘기면 REST 정본을 다시 조회한다.

**Outbox**: 사용자에게 성공을 반환해야 하는 상태 변경과 이벤트를 **같은 트랜잭션**에 기록한다. 알림·검색 색인·렌즈 주석·추천 이유 생성은 outbox 소비자가 재시도한다. 같은 이벤트가 두 번 와도 외부 효과는 한 번만 발생해야 한다.

**AI 결과는 영속 상태 전이의 유일한 조건이 될 수 없다.** 실패 시 결정적 폴백이나 사용자 입력으로 계속 진행한다.

---

# 9. 보안 · 프라이버시 · 안전

## 9.1 인증

Argon2id · access 15분(`sub`·`session_id`·`token_version`만 담는다) · refresh는 해시만 저장하고 매번 회전, 재사용 탐지 시 token family 전량 폐기 · 팀 권한은 토큰에 넣지 않고 요청 시 DB/Redis에서 확인.

## 9.2 객체 권한 (IDOR)

모든 repository 쿼리에 `AuthorizationContext(user_id, acting_profile_id, roles)`가 필요하다. resource ID만으로 조회하는 public repository를 도메인 서비스에 노출하지 않는다.

필수 테스트: 다른 팀 명의 시그널 생성 금지 · 다른 시그널의 비공개 지원 목록 조회 금지 · 협업 비멤버의 메시지 조회·렌즈 호출 금지 · 타인의 자격 파일 presigned URL 발급 금지 · 일반 사용자의 보증금 결의 API 호출 금지.

## 9.3 업로드

10분 presigned URL → object key는 **서버가 생성** → 업로드 후 malware scan + 실제 MIME 검사 → scan 전 상태는 `QUARANTINED`(공개·AI 전달·검토 UI 사용 금지).

## 9.4 PII와 AI 전달표

| 데이터 | 저장 | AI 전달 | 로그 |
|---|---|---|---|
| 요청·메시지 원문 | 암호화 | 목적상 허용 | hash만 |
| 표시 이름 | 정책별 | 금지 | resource ID만 |
| 이메일·전화번호 | 암호화 | 금지 | 금지 |
| 도시·UTC offset | 저장 | 도시/offset만 허용 | 코드만 |
| 정밀 좌표 | 별도 암호화 | 금지 | 금지 |
| 자격증·포트폴리오 원본 | object storage | **금지** | object ID만 |
| 추천 점수·순위 | 저장 | 금지 | 정책 버전만 |
| 신뢰 값 | 저장 | 금지 | 버전만 |
| 보증금 실제 금액 | 저장 | 값 금지, 슬롯 이름만 | 금액 없는 코드 |

## 9.5 모더레이션과 안전 분기

- `/ai/parse`·`/ai/lens`·`/ai/guard`·`/ai/translate`·`/ai/search-normalize` **전에** `omni-moderation-latest`를 호출한다(무료).
- **자해 계열이 플래그되면 AI 파이프라인을 태우지 않는다.** locale별 위기 지원 상수로 즉시 분기한다. 이건 "표현" 문제가 아니다.
- 그 외 플래그는 시그널 `PENDING_REVIEW` · 메시지 `HELD_FOR_REVIEW` · 평가 `PENDING_MODERATION`으로 저장한다. **AI는 차단 권한을 갖지 않는다.**
- 의료·법률 고지문은 **결정적 상수**다. 언어별 번역본을 fixture로 고정하고 런타임 모델 생성 경로를 통과시키지 않는다.

```python
DISCLAIMER = {
  "MEDICAL": "이 안내는 의료 행위가 아니며 진단·처방을 대체하지 않습니다. "
             "응급 상황이면 현지 응급번호로 즉시 연락하세요.",
  "LEGAL":   "이 안내는 법률 자문이 아닙니다.",
}
```

부착 조건: `required_credentials`에 `MEDICAL_LICENSE`/`LEGAL_LICENSE`가 있거나 `signal_type=HELP ∧ urgency=CRITICAL`.

## 9.6 문화 고정관념 방지 3중

1. **데이터** — `scope_locale`은 언어권, `scope_context`는 상황. 개인 속성이 KB에 없다.
2. **프롬프트** — "개인을 국적으로 단정하지 말고 경향으로 서술하라".
3. **출력** — 단정 표현 린트. **셋 중 마지막만 보증이다.**

`TABOO_*` 주석에는 린트를 더 세게 건다 — 경향 표지에 더해 「상대에 따라 다를 수 있어요」류 **유보 문구를 필수**로 요구한다. 그리고 `disputes[]`(「우리는 안 그래요」 창구)는 확신도를 실제로 깎는다. 형식적 창구가 아니다.

## 9.7 감사 로그

팀 권한 변경 · 자격 검토 결정 · 시그널 발행/수정/취소 · 지원 수락과 협업 상태 변경 · **경고 무시 발신** · 모더레이션 결정 · 보증금 동의·명령·결의 · 평가 숨김 · 정책 버전 변경.
감사 로그는 원문 대신 전후 hash와 상태 enum을 저장한다.

---

# 10. 시드 데이터 (데모가 돌기 위한 최소분)

## 10.1 문화 KB — 최소 16건 · 언어권 5개 (ko · en · ja · de · pt)

**시연 필수 6건**

| ID | 언어권 | 맥락 | claim |
|---|---|---|---|
| `DE-014` | de | 업무 피드백 | 직설적 지적은 사안 중심인 경우가 많다 |
| `DE-021` | de | 회의 문화 | 회의 시각은 문자 그대로 해석되는 편이다 |
| `JP-007` | ja | 의사 표현 | 정중한 보류가 거절로 기능하는 경우가 많다 |
| `PT-003` | pt | 관계 형성 | 스몰토크가 신뢰 형성에 중요한 편이다 |
| `KO-001` | ko | 의사 표현 | "검토해보겠다"가 완곡한 보류로 쓰이는 경우가 많다 |
| `EN-005` | en | 업무 피드백 | 완곡한 제안형 표현이 사실상 지시로 읽히는 경우가 있다 |

**금기 맥락 10건** — `호칭·경칭` / `민감 화제` 두 맥락 × ko·en·ja·de·pt 5개 언어권. 데모의 「Sato씨 호칭」 경고(`JP-0xx` · 호칭·경칭)가 여기서 나온다. **이 10건이 없으면 03 문화 국경 기능이 게이트에서 전부 막혀 아무것도 뜨지 않는다.**

모든 레코드는 출처 2건 이상 교차 확인. `status='ACTIVE'`인데 출처가 1건이면 DB CHECK 제약이 막는다.

> **홈 화면의 카불 HELP 시그널(다리어)은 KB가 없는 언어권이다.** 이건 결함이 아니라 **시연 자산**이다 — 근거가 없으므로 문화 주석이 아예 뜨지 않고, 직역만 나간다. "근거 없으면 침묵한다"는 원칙(§2.4-2)을 화면에서 그대로 보여줄 수 있는 유일한 자리이므로 **일부러 남긴다.** 심사에서 "지원 안 하는 언어는 어떻게 되나요"라는 질문을 이 화면이 선점한다.

## 10.2 데모 계정·데이터

| 항목 | 값 |
|---|---|
| 사용자 | 이민석(ko, 서울) · L. Weber(de, 베를린) · M. Sato(ja, 도쿄) · A. Costa(pt, 리스본) · J. Kim(ko, 서울) 외 직접 찾기용 24명 |
| 신뢰 온도 시드 | 37.3 / 41.2 / 39.8 / 38.1 (`is_demo=true`) |
| 시그널 | EVA 팬게임 WORK(역할 3개) · 카불 새벽 병원 HELP(CRITICAL·현장·의료) · 레트로 게임 음악 CIRCLE · 밴드 페스티벌 BOOKING(`target_is_team=true`) |
| 협업 | EVA 팬게임 크루 3인, 보증금 1인 ₩100,000 × 3 = ₩300,000 |
| 결과물 | 기획서 v1.3.pdf · 플레이 가능한 빌드.apk · 캐릭터 시트 12종.zip · 소개 영상.mp4 (각 해시) |
| 메시지 | 목업 채팅 4건(독일어 직설 · 내 응답 · 일본어 보류 · 줄임말 번역 실패) |

시드는 `scripts/seed_demo.py` 하나로 멱등하게 실행된다. 두 번 돌려도 데이터가 중복되지 않는다.

---

# 11. 테스트 전략과 CI 차단선

## 11.1 테스트 층

| 층 | 대상 | 환경 |
|---|---|---|
| unit | 상태 전이, 정책, 금액, 역할 동일성, 슬롯 치환, trust.v1 | DB 없음 |
| repository | SQL 제약·인덱스·암호화 컨버터 | 임시 PostgreSQL+pgvector |
| contract | OpenAPI, AI Pydantic 스키마, 이벤트 스키마 | `AI_MODE=stub` |
| integration | DB+Redis+object/payment fake + AI stub | Docker Compose |
| e2e | 프론트 핵심 흐름 (Playwright) | 로컬 dev |
| AI eval | 30문항 평가셋 | stub은 매 PR, live는 수동 |
| security | authz/IDOR, secret/PII lint | 매 PR |

## 11.2 AI 평가셋 30문항 (합격선 ≥ 27/30)

| 모듈 | 문항 | 대표 검증 |
|---|---|---|
| M1 파서 | 9 | P01 팬게임(역할 폼 비었을 때 `roles_requested=[]`) · P05 숫자 미언급 시 null(**환각 금지**) · P08 자해 암시 시 파서 미호출 · **P09 역할 3개 입력 + 4번째 암시 → 정확히 3건, AI 추가분 0** |
| M2 렌즈 | 8 | L03 근거 없는 언어권 → 미표시 · L04 존재하지 않는 KB ID → 폐기 · L06 단정 표현 → 린트 탈락 · L08 단순 인사말 → 과잉 주석 억제 |
| M3 가드 | 5 | G02 정상 문장 → `risk=NONE`(과잉 경고 억제) · G03 거절이 수락으로 바뀌지 않음 · **G04 실례 호칭 → LOW여도 표시 + 유보 문구** · G05 근거 없는 금기 추정 → 미표시 |
| M4 번역 | 3 | T01 숫자 다중집합 보존 · T02 speech act 유지 · T03 관용구 등재 |
| M5 RAG | 2 | K01 언어권 하드 필터 · K02 `DE-014 → 0.58` 골든 테스트 |
| M6·M7·M8 | 3 | W01 슬롯 밖 숫자 0 · D01 금액·비율 필드 부재 · Q01 다국어 동의어 확장 |

채점: 결정적 판정(enum·불리언·필드 존재·ID 집합·숫자 다중집합) 26문항은 코드 비교. 문장 품질 4문항만 LLM-judge(루브릭 3항 × 0–2점, 합 4점 이상 통과).

## 11.3 하드 실패 조건 — 하나라도 걸리면 머지 차단

1. OpenAPI 생성 실패 또는 승인되지 않은 breaking diff
2. Alembic head 불일치 또는 빈 DB migration 실패
3. AI schema version 불일치
4. `signal_roles.source`에 `USER_FORM` 이외 값 1건 이상
5. 역할 폼과 AI 결과의 multiset 불일치를 저장한 케이스 1건 이상
6. AI가 새로 만든 판정 숫자 1건 이상 (발행 가능한 자연어의 슬롯 밖 숫자, 점수·순위·보증금 금액·정산 비율 필드)
7. 근거 없는 L3·가드 발행 1건 이상
8. 번역 숫자 다중집합 불일치 1건 이상
9. 허용되지 않은 aggregate 상태 전이 1건 이상
10. 동일 멱등성 키로 외부 효과가 두 번 발생
11. 보증금 원장 불균형 또는 provider event 중복 반영
12. `resolved_by_type='AI'`를 허용하는 코드·migration 발견
13. 프론트 번들 또는 레포에서 `OPENAI_API_KEY` · OpenAI 직접 URL 발견
14. 메시지·이메일·전화번호·토큰 원문이 로그·fixture에 존재
15. `AI_MODE=stub` 통합 테스트가 OpenAI 키 없이 실패
16. `kb_norms.embedding` 차원이 1536이 아님
17. 운영자 아닌 사용자가 자격·모더레이션·보증금 결의 API 접근 가능
18. 의료·법률 고지문이 런타임 AI 생성 경로를 통과
19. AI 평가셋 정확도 27/30 미만
20. `guard_events`에서 `trust_events`를 생성하는 경로 존재
21. `skills[].importance`가 저장·표시·랭킹에 유입

## 11.4 필수 계약 테스트 이름 (그대로 만든다)

```text
test_ai_routes_return_envelope_without_double_wrapping
test_ai_schema_versions_match_manifest
test_parse_roles_equal_exact_user_form_multiset
test_parse_missing_numbers_remain_null
test_no_ai_designed_roles
test_signal_publish_requires_inference_confirmation
test_parse_importance_metadata_never_reaches_matching_or_storage
test_recommendation_excludes_culture_distance_and_trust
test_search_normalizer_cannot_set_rank_or_weight
test_evidence_gate_no_kb_no_annotation
test_schema_violation_discards_and_falls_back
test_ai_never_produces_judgments
test_message_guard_hash_matches_final_text
test_guard_ignore_does_not_emit_trust_event
test_translation_preserves_numerals_or_falls_back_to_original
test_deposit_has_no_work_payment_or_split_fields
test_deposit_webhook_is_idempotent
test_deposit_ledger_balances_per_currency
test_deposit_resolution_rejects_ai_actor
test_self_harm_route_skips_ai_pipeline
test_high_risk_disclaimer_is_constant
test_trust_projection_is_deterministic_and_excludes_guard_events
test_stub_mode_requires_no_openai_key
test_embedding_dimension_is_1536
test_judge_model_not_in_runtime
test_no_hardcoded_model_id
test_logs_contain_no_raw_pii
```

## 11.5 통합 시나리오 (E2E 필수 통과)

| ID | 시나리오 | 필수 결과 |
|---|---|---|
| B01 | 스킬 없는 사용자가 WORK 요청 | 통합 계정으로 DRAFT·OPEN 가능 |
| B02 | 역할 폼 비어 있는 팬게임 요청 | 역할 0건, 라이선스 경고, 숫자 null |
| B03 | 역할 3개 + 암시된 4번째 | 저장 역할 **정확히 3개** |
| B04 | 새벽 병원 HELP | CRITICAL·현장·의료 고지, 자해 분기와 혼동 없음 |
| B05 | 팀 밴드 BOOKING | 팀 대상 검색·초대 가능 |
| B06 | CIRCLE 모집 | 여러 지원 수락, 정원에서 close |
| B07 | 직접 다국어 검색 | M8 실패해도 원 질의로 결과 반환 |
| B08 | 추천 실행 | 점수·순위는 서버 생성, AI에는 슬롯 이름만 |
| B09 | 가드 경고 무시 발신 | 메시지 전달, guard audit 기록, **trust event 없음** |
| B10 | 번역 숫자 변경 | 재번역 실패 후 원문 병기 |
| B11 | 근거 없는 문화 추정 | L1만, L3 영역 자체 미렌더 |
| B12 | 정상 완료 보증금 | LOCKED → REFUND_PENDING → REFUNDED |
| B13 | 보증금 webhook 중복 | 원장 entry 1건 |
| B14 | 과실 결의에 AI actor 시도 | 422 / DB 차단 |
| B15 | `TRUST_POLICY_VERSION=disabled` | 200, value null, UNAVAILABLE 화면 |
| B16 | OpenAI 키 없이 전체 데모 | 6화면 전부 렌더, 간이 모드 배지 표시 |

---

# 12. 저장소 구조와 툴체인

## 12.1 디렉터리

```text
pangaea/
├─ .husky/                    # pre-commit · commit-msg · pre-push
├─ .github/workflows/ci.yml
├─ docker-compose.yml         # postgres(pgvector) · redis · minio · backend
├─ package.json               # 루트 워크스페이스 (husky·lint-staged·commitlint)
├─ docs/
│  ├─ SPEC.md                 # 이 문서
│  ├─ PROGRESS.md             # ★ 태스크 진행 기록 (세션 인계용)
│  ├─ DECISIONS.md            # 진행 중 내린 가정·결정
│  └─ QA/                     # 검수 에이전트 리포트 3종
├─ frontend/
│  ├─ app/
│  │  └─ [locale]/            # next-intl 라우팅 (ko | en)
│  │     ├─ (auth)/login · signup
│  │     ├─ (app)/home · write · who · chat · done · find
│  │     │        · profile · team · applications · deposit · notifications
│  │     ├─ demo/             # 폰 프레임 시연 페이지 (§4.7-6)
│  │     └─ api/              # BFF 프록시 (필요 시)
│  ├─ components/
│  │  ├─ shell/               # AppShell · MobileShell · DesktopShell · SideNav · TabBar
│  │  ├─ ui/                  # 목업 컴포넌트 1:1 이식 (chip·btn·card·row·av·fold·note)
│  │  └─ feature/             # 화면별 조합 컴포넌트
│  ├─ lib/api/                # OpenAPI 생성 클라이언트 (수기 DTO 금지)
│  ├─ lib/ws/
│  ├─ i18n/                   # next-intl 설정 · locale 감지
│  ├─ messages/ko.json        # 원본 문구
│  ├─ messages/en.json        # 번역본 — 키 집합이 ko와 완전히 같아야 한다
│  ├─ styles/tokens.css       # §4.2 토큰
│  └─ e2e/                    # Playwright (ko·en × 모바일·데스크톱)
├─ backend/
│  ├─ app/
│  │  ├─ main.py settings.py
│  │  ├─ api/v1/{auth,profiles,teams,credentials,signals,search,applications,
│  │  │           collaborations,chat,deposits,reviews,operations,health,ws,ai}.py
│  │  ├─ domains/{identity,profiles,credentials,signals,discovery,applications,
│  │  │           collaborations,chat,deposits,reputation,moderation}/
│  │  │           # 각 폴더: models.py schemas.py service.py repository.py events.py
│  │  ├─ integrations/{ai_gateway,deposit_provider,object_storage,notifications}.py
│  │  ├─ policies/{matching,credential,deposit,completion,trust}.py
│  │  └─ platform/{db,redis,crypto,idempotency,outbox,audit,logging,metrics,security}.py
│  ├─ migrations/versions/
│  ├─ tests/{unit,contract,integration,security}/
│  └─ scripts/{check_openapi_breaking,check_ai_contracts,check_no_direct_openai,seed_demo}.py
└─ ai/
   └─ pangaea_ai/
      ├─ config.py client.py envelope.py router.py moderation.py
      ├─ schemas/{parse,lens,guard,translate,why,deposit,search,kb}.py
      ├─ prompts/{parse.v2,lens.v2,guard.v2,translate.v1,why.v2,deposit.v1,search.v1}.txt
      ├─ modules/{parse,lens,guard,translate,why,deposit,search}.py
      ├─ rag/{embed,search,confidence}.py
      ├─ gates/{evidence,stereotype,no_numbers,slots,translation}.py
      ├─ fallback/
      ├─ fixtures/ai/
      ├─ evals/{cases.yaml,run.py,judge.py}
      └─ kb/seeds/
```

**단일 소스 원칙**: JSON Schema를 손으로 쓰지 않는다. Pydantic v2 모델에서 `model_json_schema()`로 생성하고 strict 요구사항(`additionalProperties:false`, 전 필드 required)을 후처리기가 강제한다.

## 12.2 브랜치·커밋

- `feature/<태스크ID>-<요약>` → PR → `develop`. `main`은 사람이 지시할 때만.
- Conventional Commits: `feat(signals): T-14 발행 게이트 9종 검증 추가`
- 커밋 전 `git add -A && git -c core.quotepath=false diff --cached --stat`로 신규 파일 포함 확인.

## 12.3 Husky · Prettier · ESLint (필수)

```bash
pnpm add -D -w husky lint-staged prettier eslint @commitlint/{cli,config-conventional} \
            eslint-config-next @typescript-eslint/{parser,eslint-plugin} \
            eslint-plugin-tailwindcss prettier-plugin-tailwindcss
pnpm --filter frontend add next-intl
pnpm exec husky init
```

`.husky/pre-commit`

```sh
pnpm exec lint-staged
```

`.husky/commit-msg`

```sh
pnpm exec commitlint --edit "$1"
```

`.husky/pre-push`

```sh
pnpm --filter frontend typecheck
pnpm --filter frontend lint
cd backend && ruff check . && python -m pytest -q -m "not live"
```

`package.json` → `lint-staged`

```json
{
  "*.{ts,tsx,js,jsx}": ["prettier --write", "eslint --fix --max-warnings=0"],
  "*.{json,md,css,yml,yaml}": ["prettier --write"],
  "*.py": ["ruff check --fix", "ruff format"]
}
```

ESLint 규칙 추가 (불변 규칙의 프론트 방어선):

```jsonc
{
  "rules": {
    "no-restricted-imports": ["error", { "patterns": ["openai", "@anthropic-ai/*"] }],
    "no-restricted-syntax": [
      "error",
      { "selector": "Literal[value=/^sk-/]",
        "message": "API 키를 프론트에 두지 않는다" },
      { "selector": "JSXText[value=/[가-힣]/]",
        "message": "화면 문구는 messages/*.json에서 가져온다 (§4.8)" }
    ],
    "@typescript-eslint/no-explicit-any": "error"
  }
}
```

추가 검사 스크립트 `scripts/check_i18n_parity.mjs` — `messages/ko.json`과 `en.json`의 키 집합을 비교해 하나라도 어긋나면 종료 코드 1. `pre-push`와 CI `lint` 잡에 연결한다.

**훅을 `--no-verify`로 건너뛰지 않는다.** 실패하면 고쳐서 통과시킨다.

## 12.4 CI 파이프라인

```yaml
jobs:
  lint:      # prettier --check · eslint · ruff · commitlint
  typecheck: # tsc --noEmit · mypy(선택)
  backend:   # pytest (AI_MODE=stub, OPENAI_API_KEY 미주입) + alembic upgrade head on empty db
  contract:  # openapi diff · ai schema manifest · scripts/check_no_direct_openai.py
  ai-eval:   # evals/run.py --mode stub
  e2e:       # playwright (seed_demo 후)
  guards:    # §11.3 하드 실패 조건 21종 스캐너
```

---

# 13. 작업 분해 — 최소 단위 태스크 50개

**규칙**
- 위에서부터 순서대로 하나씩 처리한다. (T-47·T-48은 P0 끝, T-49·T-50은 P8 끝에서 실행한다)
- 태스크마다 DoD를 만족하는 테스트를 작성·실행하고 **통과한 뒤에만** 커밋한다.
- 커밋 직후 `docs/PROGRESS.md`에 한 줄 추가: `- [x] T-07 프로필/스킬 API — 2026-08-13 · 커밋 abc1234 · 테스트 12 pass`
- 세션이 끊기면 다음 세션은 PROGRESS.md의 마지막 `[x]` 다음부터 이어받는다.

## P0. 기반 (T-01 ~ T-06)

| ID | 태스크 | DoD |
|---|---|---|
| T-01 | 레포 초기화 · 워크스페이스 · Husky/Prettier/ESLint/commitlint | 훅 3종이 실제로 발동하고, 일부러 깨뜨린 커밋이 차단된다 |
| T-02 | docker-compose (postgres+pgvector · redis · minio) | `docker compose up -d` 후 `CREATE EXTENSION vector` 성공 |
| T-03 | FastAPI 스켈레톤 · settings · 공통 봉투 · 오류 핸들러 · `/health/live`·`/health/ready` | ready가 DB·Redis 연결과 migration 일치를 확인 |
| T-04 | Alembic 초기 migration (users · profiles · skills · 언어 · availability) | 빈 DB에서 upgrade head 성공, downgrade 성공 |
| T-05 | Next.js 스켈레톤 · 토큰 CSS 이식 · 폰 프레임 레이아웃 · 탭 4종 | 목업과 색·간격이 픽셀 단위로 대응 (스크린샷 비교) |
| T-06 | 공통 컴포넌트 이식 (chip · btn · card · row · av · sec · gap · note · fold) | Storybook 없이도 `/dev/components` 페이지에서 전 변형 확인 |
| T-47 | **i18n 골격** — next-intl · `[locale]` 라우팅 · `messages/{ko,en}.json` · 언어 전환 UI · parity 검사 스크립트 | JSX 한글 리터럴 ESLint 규칙 발동 확인, 키 불일치 시 스크립트가 종료 코드 1 |
| T-48 | **데스크톱 셸** — `AppShell` 분기 · `SideNav`(탭 승격) · 카드 폭 상한 · 대화 3단(≥1440px) | 페이지 컴포넌트에 폼팩터 분기 코드 0건, 4개 브레이크포인트 스크린샷 확보 |

## P1. 인증·프로필 (T-07 ~ T-12)

| ID | 태스크 | DoD |
|---|---|---|
| T-07 | 가입·로그인·refresh 회전·재사용 탐지 | 재사용 시 family 폐기 테스트 통과 |
| T-08 | `acting_profile_id` 기반 권한 컨텍스트 · IDOR 가드 | §9.2 5종 테스트 통과 |
| T-09 | 개인 프로필 CRUD · 스킬/언어/가능시간 PUT | 카탈로그 자동완성 동작 |
| T-10 | 업로드(presigned) · 자격 제출 · 포트폴리오 | QUARANTINED 상태에서 공개·AI 전달 차단 |
| T-11 | 팀 프로필 · 멤버 초대/수락/권한 | 마지막 OWNER 제거 409 |
| T-12 | 프론트 S00 로그인/가입 · S07 프로필 · S08 팀 | 폼 검증 인라인, 새로고침 후 세션 유지 |

## P2. AI 레이어 뼈대 (T-13 ~ T-19)

| ID | 태스크 | DoD |
|---|---|---|
| T-13 | `pangaea_ai` 패키지 · config · client(재시도·타임아웃·usage 회계) · 봉투 | 모델 ID 하드코딩 린트 통과 |
| T-14 | 3중 모드(live/replay/stub) · fixture 키 해시 | 키 없이 stub 전 모듈 응답 |
| T-15 | Pydantic 스키마 7종 + strict JSON Schema 생성기 | 생성된 스키마가 strict 규칙 전부 만족 |
| T-16 | 게이트 5종 (evidence · stereotype · no_numbers · slots · translation) | 각 게이트 단위 테스트 |
| T-17 | 모듈별 결정적 폴백 8종 | AI 없이 전 모듈이 유효 결과 반환 |
| T-18 | 모더레이션 전처리 · 자해 분기 · 고위험 고지 상수 | 자해 입력 시 AI 미호출 검증 |
| T-19 | KB 테이블 · 임베딩(1536 축약+재정규화) · 5단 검색 · 시드 16건 | `DE-014 → 0.58` 골든 테스트 |

## P3. 시그널 (T-20 ~ T-25)

| ID | 태스크 | DoD |
|---|---|---|
| T-20 | M1 파서 모듈 + 프롬프트 + few-shot | P01·P05·P09 통과 |
| T-21 | `/ai/parse` 어댑터 (역할 multiset 재검증 · evidence substring · importance 폐기) | 역할 불일치 시 폴백 배열 사용 |
| T-22 | 시그널 DRAFT 생성 · override 허용 경로 · revision | 역할은 override 불가 검증 |
| T-23 | 발행 게이트 9종 · 오류 코드 | B02·B03 통과 |
| T-24 | 프론트 S02 + S02a 추정 시트 + S02b 역할 시트 | 점선 배지·확인 없이는 발행 버튼 비활성 |
| T-25 | 프론트 S01 홈 · S12 시그널 상세 | 유형 칩 필터·도시 스트립 동작 |

## P4. 검색·추천 (T-26 ~ T-29)

| ID | 태스크 | DoD |
|---|---|---|
| T-26 | M8 검색 정규화 + `/search/profiles` (hard filter + 사전식) | M8 실패해도 원 질의로 결과 (B07) |
| T-27 | 추천 실행 · `recommendations` 저장 · 정책 버전 노출 | 문화·신뢰·confidence 미유입 테스트 |
| T-28 | M6 추천 이유 (슬롯 방식 + 조사 처리) | 슬롯 밖 숫자 0, 미치환 0 |
| T-29 | 프론트 S03 + S03a 프로필 상세 + S06 직접 찾기 + 순서 설명 패널(§4.6-B) | 패널이 서버 정책을 렌더 |

## P5. 지원·협업·보증금 (T-30 ~ T-35)

| ID | 태스크 | DoD |
|---|---|---|
| T-30 | 지원/초대 생성 · 수락 트랜잭션(협업+멤버+대화 원자적) | 정원 초과 409 |
| T-31 | 협업 상태 머신 · 활성화 · 완료 요청/확인/반려 | 허용 외 전이 409 |
| T-32 | 보증금 제안·동의·terms hash · 상한 검증 | 작업 대금 필드 존재 시 테스트 실패 |
| T-33 | sandbox provider · funding session · webhook 멱등 · 원장 균형 | B12·B13 통과 |
| T-34 | M7 보증금 문구 (슬롯 · clause allowlist) | 금액 필드 부재 · 주의 문구 존재 |
| T-35 | 프론트 S09 지원 목록 · S03b 초대 확인 · S10 보증금 합의 | 서명 전 예치 버튼 비활성 |

## P6. 채팅 (T-36 ~ T-40)

| ID | 태스크 | DoD |
|---|---|---|
| T-36 | M3 가드 + 디바운스 사전 계산 + 60초 캐시 | G02 과잉 경고 억제, G04 표시 |
| T-37 | M4 번역 + 숫자 다중집합 검사 + 실패 시 원문 병기 | T01·B10 통과 |
| T-38 | 메시지 발신 오케스트레이션 · 멱등성 · guard hash 신선도 | B09 (trust event 0건) |
| T-39 | M2 렌즈 비동기 후처리 + WebSocket 이벤트 | B11 (L3 미렌더) |
| T-40 | 프론트 S04 대화 + S04a 근거 시트 | 확인 패널·번역 칩·원문 토글 전부 동작 |

## P7. 완료·평가·신뢰 (T-41 ~ T-43)

| ID | 태스크 | DoD |
|---|---|---|
| T-41 | 완료 확인 → 보증금 환급 명령 → trust_events append | 이벤트 중복 방지 |
| T-42 | `trust.v1` projection + UNAVAILABLE 폴백 | 37.3→38.5 재현, B15 통과 |
| T-43 | 프론트 S05 마무리 + S05a 평가 + S11 알림 | 온도 변화 행이 실제 값으로 |

## P8. 마감 (T-44 ~ T-46)

| ID | 태스크 | DoD |
|---|---|---|
| T-44 | 평가셋 30문항 + 러너 + LLM-judge + CI 잡 | ≥27/30 |
| T-45 | 하드 실패 조건 21종 스캐너 스크립트 + CI 연결 | 일부러 위반 시 CI 실패 확인 |
| T-46 | seed_demo 멱등화 · replay fixture 동결 · README · 90초 데모 각본 | 키 없이 `docker compose up` + `pnpm dev`로 전 화면 시연 |
| T-49 | **en 문구 전수 번역** · 길이 팽창 대응 · locale 숫자/날짜 포맷 | ko/en 키 parity 100%, en에서 버튼·칩·탭 넘침 0건 |
| T-50 | **폼팩터 × 언어 조합 E2E** — (모바일·데스크톱) × (ko·en) 4벌 | §11.5 B01~B16이 4개 조합 전부에서 통과 |

---

# 14. 검수 에이전트 3종 — 전부 PASS할 때까지 반복

구현이 끝나면 아래 세 에이전트를 **동시에** 띄운다. 각자 `docs/QA/agent{1,2,3}-<회차>.md`에 리포트를 남긴다.
**하나라도 FAIL이면 수정 후 세 에이전트를 처음부터 다시 전부 돌린다.** 부분 재검사로 끝내지 않는다.

## 14.1 에이전트 1 — 본질 검수 (명세·결정 사항 대비)

> **프롬프트**: 너는 PANGAEA 명세 감사관이다. `docs/SPEC.md`와 구현 코드를 대조해, 명세의 본질에서 벗어난 기능·코드가 있는지 찾아라. 발견 사항만 보고하고 고치지 마라.

점검 목록:

1. **불변 규칙 위반** — §2의 8개 규칙 각각에 대해 위반 코드 경로가 있는가.
2. **AI 판정 유입** — AI 출력이 점수·순위·신뢰값·보증금 금액·과실·역할로 저장·표시된 경로가 있는가.
3. **역할 계약** — `signal_roles.source`가 `USER_FORM` 외 값을 가질 수 있는가. multiset 검증이 실제로 실행되는가.
4. **없어야 할 것이 생겼는가** — 작업 대금·정산·지분·비율 필드, 에스크로 개념, AI 역할 설계, 문화 거리 기반 감점.
5. **요구되지 않은 기능** — 명세에 없는데 만들어진 화면·API·테이블. (범위 확장은 감점이다)
6. **누락** — §3.2 화면 인벤토리와 §6.2 엔드포인트 목록 중 구현되지 않은 항목.
7. **§1.5 충돌 해소 8건**이 결론대로 구현됐는가 (특히 A 신뢰 온도, B 순서 설명 패널).
8. **미정 항목 비의존** — 신뢰 계산식·매칭 가중치·과실 주체가 확정되지 않아도 서비스가 도는가.

**PASS 조건**: 위 8개 항목에서 심각도 High 발견 0건, Medium 발견은 사유와 함께 `docs/DECISIONS.md`에 기록되어 있을 것.

## 14.2 에이전트 2 — 동작 검수 (버튼과 하위 페이지 전수)

> **프롬프트**: 너는 QA 엔지니어다. 앱을 실제로 띄우고 Playwright로 모든 인터랙션을 눌러라. §3.2 화면 인벤토리의 "도달해야 할 곳" 열이 테스트 케이스다. 누르면 아무 일도 일어나지 않는 요소를 전부 찾아라.

점검 목록:

1. **전 버튼 클릭 커버리지** — 각 화면의 모든 `button`·`a`·`[role=button]`·탭·칩을 눌러 보고, 기대 화면 전이 또는 상태 변화가 실제로 일어나는지 확인. 죽은 버튼 0건.
2. **하위 페이지 도달** — S02a · S02b · S03a · S03b · S04a · S05a · S12까지 전부 도달·복귀 가능한가. 뒤로 가기 후 상태가 보존되는가.
3. **핵심 흐름 E2E** — §11.5의 B01~B16을 실제 브라우저에서 재현.
4. **실패 경로** — AI 없이(stub) 전 화면 렌더 · 번역 실패 칩 · 근거 없는 주석 미렌더 · `UNAVAILABLE` 온도 · 간이 모드 배지 · 409/422 오류 인라인 표시.
5. **경계 입력** — 4,000자 초과 원문, 역할 9개, 인원 0/51, 빈 검색어, 중복 지원, 만료된 토큰.
6. **콘솔·네트워크** — 브라우저 콘솔 error 0건. 실패한 네트워크 요청 0건. 키가 번들에 노출 0건.
7. **새로고침·재연결** — 각 화면에서 새로고침해도 동일 상태. WebSocket 끊었다 붙였을 때 메시지 유실 0건.
8. **폼팩터 × 언어 4벌** — (390px 모바일 · 1440px 데스크톱) × (ko · en) 조합에서 1~7번을 **전부 다시** 돌린다. 특히 데스크톱에서 하단 탭이 사라지고 좌측 내비가 뜨는지, 좌측 내비의 4항목이 모바일 탭과 같은 목적지로 가는지 확인한다.
9. **언어 전환 유지** — 언어를 바꿔도 현재 화면·스크롤·입력 중이던 폼 값이 유지되는가. 전환 후 새로고침해도 선택 언어가 유지되는가.

**PASS 조건**: 죽은 버튼 0 · B01~B16이 **4개 조합 전부**에서 통과 · 콘솔 error 0 · 미도달 하위 페이지 0.

## 14.3 에이전트 3 — 디자인 QA (고아 문자 · 겹침 · 어긋남)

> **프롬프트**: 너는 UI 품질 감독이다. 각 화면을 **360 · 390 · 414 · 768 · 1024 · 1440px** 폭에서, **ko와 en 두 언어로** 스크린샷을 찍고 DOM을 계측해 조판과 레이아웃 결함을 찾아라. 원본 목업 `PANGAEA_데모_수정.html`이 모바일 정답지다.

점검 목록:

1. **고아 문자 0건** — 마지막 줄에 한 글자(또는 한 음절 어절)만 남은 텍스트 블록. 모든 `h1/h2/p/span/button` 텍스트를 계측한다.
2. **고아 줄바꿈 0건** — 어절 중간에서 끊긴 한글. `word-break: keep-all`이 적용되지 않은 요소. **en에서는 반대로** `overflow-wrap: break-word`가 걸려 긴 단어가 컨테이너를 밀어내지 않는지 본다.
3. **겹침 0건** — 형제 요소의 bounding box가 교차하는 경우. 특히 하단 탭(68px)·채팅 입력창(bottom 68px)·확인 패널의 3중 스택.
4. **잘림 0건** — `scrollWidth > clientWidth`인데 `overflow` 처리가 없는 요소, 말줄임 없이 잘린 텍스트.
5. **토큰 준수** — 하드코딩된 hex 색이 §4.2 토큰 밖에 있는가. AI 기본값(보라 그라데이션·Inter·균일 카드 그리드)이 섞였는가.
6. **대비** — 전 텍스트/배경 조합 WCAG AA(4.5:1, 큰 글자 3:1) 통과.
7. **컴포넌트 계약 6종**(§4.4) 위반 — 버튼 높이 어긋남, `.sec` 클래스 충돌, inline 요소에 height, `.bar` 이름 충돌, 입력창 위치, 채팅 하단 여백.
8. **문구 규칙**(§4.5) — 화면에 개발 용어(L1/L3/M1/degraded/스키마/모듈/엔드포인트)가 노출됐는가. 1건이라도 있으면 FAIL.
9. **목업 대조** — S01·S02·S03·S04·S05·S06 스크린샷을 원본 HTML과 나란히 비교. 색·간격·위계가 눈에 띄게 달라진 곳.
10. **데스크톱 셸 규격**(§4.7) — ≥1024px에서 하단 탭이 사라지고 좌측 내비가 뜨는가 · 카드 폭이 640px를 넘는가 · 목록이 멋대로 2열 그리드가 됐는가 · 텍스트 줄 길이가 90자를 넘는가 · 폰 프레임/가짜 상태바가 실제 화면에 남아 있는가.
11. **en 넘침** — 영어에서 버튼·칩·탭·배지 라벨이 잘리거나 2줄로 터지는 곳. 특히 「함께하자고 하기」·「보내기 전에 한 번만 확인해 주세요」·「약속 보증금 전액 돌려드려요」의 영문 대응.
12. **문서 다이어그램** — 이 명세서와 README의 mermaid가 렌더될 때 노드 라벨끼리, 라벨과 화살표가 겹치지 않는지 확인한다. 겹치면 라벨을 줄이거나 표로 내린다.

**PASS 조건**: 1~4번 각각 0건 · 8번 0건 · 5·6·7·10·11·12번 위반 0건 · 9번 시각 회귀 없음. **6개 폭 × 2개 언어 = 12벌 전부에서 만족해야 한다.**

## 14.4 반복 규칙

```
구현 완료
   ↓
에이전트 1·2·3 동시 실행
   ↓
전부 PASS?  ──아니오──▶ FAIL 항목 수정 → 커밋 → PROGRESS.md 기록 → 처음으로
   │예
   ▼
최종 보고 (결론 먼저: 무엇을 만들었고 무엇이 통과했나)
```

라운드마다 `docs/QA/round-N-summary.md`에 세 리포트의 요약과 조치 내역을 남긴다. 라운드가 5회를 넘어가면 남은 FAIL 항목과 그 원인을 사람에게 보고하고 판단을 구한다.

---

# 15. 완료 정의 (Definition of Done)

이 프로젝트가 "끝났다"고 말할 수 있는 조건이다. 전부 참이어야 한다.

**제품**
- 통합 계정 하나로 요청과 응답을 모두 수행한다.
- 개인·팀 프로필이 동일한 검색·지원 경로를 쓴다.
- HELP·WORK·CIRCLE·BOOKING 네 종류가 생성·발행·검색된다.
- 자동 추천과 직접 검색이 모두 동작한다.
- **역할은 사용자 폼에 있는 항목만 저장된다.**
- 가드·번역·렌즈가 실패해도 메시지 원문 경로가 유지된다.
- WORK·BOOKING 보증금 sandbox의 합의·예치·정상 환급이 재현된다.
- **작업 대금·정산·비율 기능이 존재하지 않는다.**
- 완료 → 상호 평가 → 신뢰 온도 갱신이 연결된다.

**계약**
- 프론트가 생성된 OpenAPI 클라이언트로 빌드된다(수기 DTO 0건).
- AI 스키마 7종 버전과 백엔드 어댑터 계약이 일치한다.
- AI 경로만 AI 봉투를 쓰고 이중 래핑이 없다.
- 모든 mutation의 멱등성·version conflict가 검증된다.

**안전·판정 경계**
- AI 출력의 역할·importance·confidence가 확정 역할·점수·순위·신뢰값·보증금 금액·과실 판정으로 저장·발행·사용되는 경로가 **없다.**
- 근거 없는 문화 주석 0건.
- 번역 숫자 불일치 0건이거나 원문 폴백으로 격리됨.
- 자해 신호가 AI 생성 파이프라인을 통과하지 않는다.
- 의료·법률 고지문이 상수다.
- AI 입력·로그에 금지 PII 0건.
- 보증금 원장 불균형·중복 provider event 0건.

**화면**
- 모바일(≤430px)과 데스크톱(≥1024px) 양쪽에서 모든 화면이 동작한다. 데스크톱은 좌측 내비, 모바일은 하단 탭이다.
- 페이지 컴포넌트에 폼팩터 분기 코드가 없다. 셸만 갈아 끼운다.
- UI가 ko·en 두 언어로 전환되고, 두 언어의 문구 키 집합이 완전히 같다.
- JSX에 하드코딩된 한글 문자열이 0건이다.

**운영**
- 빈 DB에서 migration·seed·startup·readiness가 성공한다.
- **OpenAI 키 없이 CI 전체가 통과한다.**
- `AI_MODE=replay`에서 fixture miss 0건, miss가 나도 stub으로 화면이 유지된다.
- `DEPOSIT_PRODUCTION_ENABLED=false`, `DEPOSIT_FORFEITURE_ENABLED=false`가 기본값이다.

**검수**
- 에이전트 1·2·3이 같은 라운드에서 동시에 PASS했고, 리포트가 `docs/QA/`에 있다.

---

# 부록 A. 환경변수

```bash
# ── 앱
APP_ENV=development
APP_BASE_URL=http://localhost:8000
FRONTEND_ORIGINS=http://localhost:3000

# ── 저장소
DATABASE_URL=postgresql+psycopg://pangaea:***@postgres:5432/pangaea
REDIS_URL=redis://redis:6379/0
FIELD_ENCRYPTION_KEY=base64:...
JWT_SIGNING_KEY=base64:...
ACCESS_TOKEN_TTL_SECONDS=900
REFRESH_TOKEN_TTL_DAYS=30

OBJECT_STORAGE_ENDPOINT=http://minio:9000
OBJECT_STORAGE_BUCKET=pangaea-private
OBJECT_STORAGE_ACCESS_KEY=...
OBJECT_STORAGE_SECRET_KEY=...
UPLOAD_MAX_BYTES=52428800

# ── 정책 버전
MATCHING_POLICY_VERSION=matching.v1
CREDENTIAL_POLICY_VERSION=credential.v1
DEPOSIT_APPLICABILITY_POLICY_VERSION=deposit-applicability.v1
DEPOSIT_CAP_POLICY_VERSION=deposit-cap.v1
COMPLETION_POLICY_VERSION=completion.v1
TRUST_POLICY_VERSION=trust.v1          # disabled 로 두면 UNAVAILABLE 경로

# ── 보증금 (데모는 sandbox 고정)
DEPOSIT_PROVIDER=sandbox
DEPOSIT_PROVIDER_API_KEY=...
DEPOSIT_PROVIDER_WEBHOOK_SECRET=...
DEPOSIT_PRODUCTION_ENABLED=false
DEPOSIT_FORFEITURE_ENABLED=false

# ── AI (서버 프로세스에만. 프론트 빌드 환경에 존재하면 CI 실패)
OPENAI_API_KEY=sk-...
PANGAEA_MODEL_LOW=gpt-5.6-luna
PANGAEA_MODEL_MID=gpt-5.6-terra
PANGAEA_MODEL_JUDGE=gpt-5.6-sol
PANGAEA_MODEL_EMBED=text-embedding-3-large
PANGAEA_EMBED_DIM=1536
AI_MODE=stub                            # live | replay | stub  (CI=stub, 시연=replay)
AI_DAILY_BUDGET_KRW=20000
AI_USD_KRW=1400
AI_L3_MIN_CONFIDENCE=0.50
AI_GUARD_MIN_CONFIDENCE=0.70
AI_TRANSLATE_MAX_EXPANSION=2.5

# ── 운영
OUTBOX_POLL_INTERVAL_MS=500
OUTBOX_MAX_ATTEMPTS=8
LOG_LEVEL=INFO
```

로그 금지 필드: 요청·메시지·평가 원문 · 이메일·전화번호·이름 · access/refresh token · OpenAI 키·provider secret · 자격증 파일 URL · 결제 수단.

# 부록 B. 화면 × API 대조표

| 화면 요소 | 담당 | 계약 |
|---|---|---|
| 「이렇게 이해했어요」 태그 | M1 | `POST /ai/parse` → `skills[]`·`duration`·`compensation`·`team_shape` |
| 점선 「추정」 배지 | M1 | `origin=INFERRED` → 발행 전 확인 필수 |
| 「필요한 역할 · 직접 정하기」 | **AI 아님** | `roles_requested[]` — 파서는 폼 입력을 통과시킬 뿐 |
| 2차 창작 안내 | M1 + 규칙 엔진 | `license_risk.flagged` |
| 「왜 추천했나요」 문장 | M6 | `POST /ai/why` — 템플릿 + 슬롯 치환 |
| 「찾으시는 역할과 조금 달라요」 | **서버** | 결정적 판정. AI 문장이 아니다 |
| 「순서는 어떻게 정해지나요?」 | **서버** | `recommendation_runs.policy_version` |
| 「원문 —」 라인 | M2 L1 | `data.l1.literal` |
| 「이렇게 읽으시면 좋아요」 | M2 L3 | `data.l3.annotation` + 발행 게이트 |
| 「왜 이렇게 알려주나요?」 시트 | M5 | `kb_norms` 레코드 6필드 |
| 「보내기 전에 한 번만 확인해 주세요」 | M3 | `risk`·`reader_reading`·`suggestion` |
| 「L. Weber는 이렇게 받았어요 —」 | M4 | `POST /ai/translate` → `data.translated` |
| 「번역 확인 필요」 칩 | M4 | `TRANSLATION_UNSAFE` → 원문 병기 |
| 약속 보증금 조건 3줄 | M7 | `POST /ai/deposit-draft` — 금액은 슬롯 |
| 신뢰 온도 숫자 | **서버** | `GET /profiles/{id}/trust` (`trust.v1`) |
| 직접 찾기 검색 | M8 + 서버 | `POST /ai/search-normalize` + `GET /search/profiles` |

# 부록 C. 90초 데모 각본

| 구간 | 화면 | 보여줄 것 | 말할 것 |
|---|---|---|---|
| 0–20s | S02 | 한 줄 입력 → 「이렇게 이해했어요」 + 점선 추정 배지 + 역할 3개 직접 입력 | "폼 20칸 대신 한 줄. **역할은 요청자가 쓰고, AI는 구조화만 합니다.**" |
| 20–40s | S03 | 후보 3인 · 「왜 추천했나요」 · 순서 설명 패널 펼치기 | "순서는 결정적 코드가 정합니다. 문화도 국적도 신뢰 온도도 순서에 안 들어갑니다." |
| 40–80s | S04 | 독일어 직설 → 문화 도우미 / 일본어 보류 → 의도 주석 / 호칭 경고 → 수정안 / 줄임말 → 번역 실패 칩 | "근거가 없으면 아무 말도 하지 않습니다. 번역에 실패하면 숨기지 않고 원문을 함께 보냅니다." |
| 80–90s | S05 | 결과물 4종 해시 · 보증금 3인 전액 환급 · 온도 37.3→38.5 · 4/4 국경 | "작업 대금은 앱 밖입니다. 앱이 잡는 건 약속뿐입니다." |

시연 당일은 `AI_MODE=replay` 고정. fixture는 리허설에서 동결한다.

---

**문서 끝** · PANGAEA 통합 개발 명세서 v1.0 · 2026-08-13
**병합 원본 5종**: 기능정리 v0.1 · AI레이어 v2.0 · 백엔드 API v1.0 · 데이터/DB v0.2 · 데모 HTML
**해소한 문서 간 충돌 8건**은 §1.5에 근거와 함께 기록되어 있다. 구현자는 §1.5의 결론만 따르면 된다.
