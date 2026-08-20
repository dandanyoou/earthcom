"""Idempotent demo seed (SPEC §10). Run twice → identical state.

    cd backend && .venv/bin/python -m scripts.seed_demo

Deterministic UUIDs (uuid5) make every row addressable across runs. The EVA
crew chat is seeded through the real send orchestration, so translations,
lens annotations, the guard event, and the failed-translation chip all come
from the same code paths the live app uses. Login for every demo account:
<email> / pangaea-demo1!
"""

import asyncio
import math
import random
import uuid
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.domains.chat import service as chat_service
from app.domains.chat.models import Conversation
from app.domains.collaborations import service as collab_service
from app.domains.collaborations.models import (
    Application,
    Collaboration,
    CollaborationDeliverable,
    CollaborationMember,
)
from app.domains.identity.models import PasswordCredential, User
from app.domains.kb.models import EMBED_DIMENSIONS, KbNorm
from app.domains.profiles.models import (
    AvailabilityRule,
    Profile,
    ProfileLanguage,
    ProfileSkill,
    Skill,
)
from app.domains.reputation.models import TrustEvent
from app.domains.signals.models import Signal, SignalRole, SignalSkill
from app.platform.crypto import PasswordService
from app.settings import get_settings
from pangaea_ai.modules import guard as m3
from pangaea_ai.modules import parse as m1

NS = uuid.UUID("00000000-0000-0000-0000-00000000ea75")  # earth-us seed namespace
PASSWORD = "pangaea-demo1!"
NOW = datetime.now(UTC)


def sid(key: str) -> uuid.UUID:
    return uuid.uuid5(NS, key)


def pseudo_embedding(seed: str) -> list[float]:
    rng = random.Random(seed)
    vector = [rng.uniform(-1, 1) for _ in range(EMBED_DIMENSIONS)]
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


PEOPLE = [
    # key, name, email, locale, city, tz, trust_seed, skills[(name, years, verified)], langs
    (
        "minseok",
        "이민석",
        "minseok@pangaea.dev",
        "ko",
        "SEOUL",
        "Asia/Seoul",
        0.8,
        [("게임 기획", 4, True)],
        [("ko", "NATIVE"), ("en", "CONVERSATIONAL")],
    ),
    (
        "weber",
        "L. Weber",
        "weber@pangaea.dev",
        "de",
        "BERLIN",
        "Europe/Berlin",
        4.7,
        [("Unity", 8, True), ("셰이더", 6, True)],
        [("de", "NATIVE"), ("en", "PROFESSIONAL"), ("ko", "BASIC")],
    ),
    (
        "sato",
        "M. Sato",
        "sato@pangaea.dev",
        "ja",
        "TOKYO",
        "Asia/Tokyo",
        3.3,
        [("캐릭터 아트", 6, True)],
        [("ja", "NATIVE"), ("en", "CONVERSATIONAL")],
    ),
    (
        "costa",
        "A. Costa",
        "costa@pangaea.dev",
        "pt",
        "LISBON",
        "Europe/Lisbon",
        1.6,
        [("사운드", 5, False)],
        [("pt", "NATIVE"), ("en", "PROFESSIONAL")],
    ),
    (
        "jkim",
        "J. Kim",
        "jkim@pangaea.dev",
        "ko",
        "SEOUL",
        "Asia/Seoul",
        2.6,
        [("Unity", 5, True), ("VFX", 4, False)],
        [("ko", "NATIVE"), ("en", "CONVERSATIONAL")],
    ),
    (
        "nowak",
        "R. Nowak",
        "nowak@pangaea.dev",
        "en",
        "KRAKOW",
        "Europe/Warsaw",
        0.4,
        [("Unity", 3, False), ("툴 개발", 3, False)],
        [("en", "PROFESSIONAL")],
    ),
    (
        "alvarez",
        "T. Alvarez",
        "alvarez@pangaea.dev",
        "en",
        "MEXICO_CITY",
        "America/Mexico_City",
        -0.1,
        [("Unity", 6, False), ("셰이더", 4, False)],
        [("en", "PROFESSIONAL"), ("es", "NATIVE")],
    ),
    (
        "nguyen",
        "H. Nguyen",
        "nguyen@pangaea.dev",
        "en",
        "HANOI",
        "Asia/Ho_Chi_Minh",
        -0.7,
        [("Unity", 4, False), ("최적화", 3, False)],
        [("en", "PROFESSIONAL"), ("vi", "NATIVE")],
    ),
    (
        "farah",
        "F. Ahmadi",
        "farah@pangaea.dev",
        "fa",
        "KABUL",
        "Asia/Kabul",
        0.3,
        [("통역", 5, False)],
        [("fa", "NATIVE"), ("en", "PROFESSIONAL")],
    ),
]
FILLERS = [
    (f"f{i:02d}", name, f"member{i:02d}@pangaea.dev", locale, city, tz, 0.0, skills, langs)
    for i, (name, locale, city, tz, skills, langs) in enumerate(
        [
            (
                "P. Silva",
                "pt",
                "LISBON",
                "Europe/Lisbon",
                [("일러스트", 2, False)],
                [("pt", "NATIVE")],
            ),
            ("K. Tanaka", "ja", "TOKYO", "Asia/Tokyo", [("사운드", 3, False)], [("ja", "NATIVE")]),
            ("S. Park", "ko", "SEOUL", "Asia/Seoul", [("영상 편집", 4, False)], [("ko", "NATIVE")]),
            (
                "A. Müller",
                "de",
                "BERLIN",
                "Europe/Berlin",
                [("Unity", 2, False)],
                [("de", "NATIVE")],
            ),
            (
                "Y. Suzuki",
                "ja",
                "TOKYO",
                "Asia/Tokyo",
                [("게임 기획", 3, False)],
                [("ja", "NATIVE")],
            ),
            ("D. Costa", "pt", "LISBON", "Europe/Lisbon", [("보컬", 6, False)], [("pt", "NATIVE")]),
            ("H. Lee", "ko", "SEOUL", "Asia/Seoul", [("드럼", 5, False)], [("ko", "NATIVE")]),
            ("M. Weiss", "de", "BERLIN", "Europe/Berlin", [("기타", 7, False)], [("de", "NATIVE")]),
            ("J. Sato", "ja", "TOKYO", "Asia/Tokyo", [("일러스트", 1, False)], [("ja", "NATIVE")]),
            ("C. Kim", "ko", "SEOUL", "Asia/Seoul", [("번역", 3, False)], [("ko", "NATIVE")]),
            (
                "R. Braun",
                "de",
                "BERLIN",
                "Europe/Berlin",
                [("셰이더", 2, False)],
                [("de", "NATIVE")],
            ),
            (
                "N. Alves",
                "pt",
                "LISBON",
                "Europe/Lisbon",
                [("React", 4, False)],
                [("pt", "NATIVE")],
            ),
        ],
        start=1,
    )
]

KB_SEEDS = [
    # id, locale, context, claim, confidence, verified_at
    ("DE-014", "de", "업무 피드백", "직설적 지적은 사안 중심인 경우가 많다", 0.74, "2026-08-05"),
    ("DE-021", "de", "회의 문화", "회의 시각은 문자 그대로 해석되는 편이다", 0.70, "2026-07-20"),
    ("JP-007", "ja", "의사 표현", "정중한 보류가 거절로 기능하는 경우가 많다", 0.78, "2026-08-01"),
    ("PT-003", "pt", "관계 형성", "스몰토크가 신뢰 형성에 중요한 편이다", 0.70, "2026-07-15"),
    (
        "KO-001",
        "ko",
        "의사 표현",
        '"검토해보겠다"가 완곡한 보류로 쓰이는 경우가 많다',
        0.72,
        "2026-08-01",
    ),
    (
        "EN-005",
        "en",
        "업무 피드백",
        "완곡한 제안형 표현이 사실상 지시로 읽히는 경우가 있다",
        0.68,
        "2026-07-25",
    ),
    ("KO-011", "ko", "호칭·경칭", "직함 생략이 무례로 읽히는 경우가 있다", 0.75, "2026-08-01"),
    ("EN-011", "en", "호칭·경칭", "첫 호칭은 성 대신 이름을 쓰는 경우가 많다", 0.73, "2026-08-01"),
    (
        "JP-011",
        "ja",
        "호칭·경칭",
        "「◯◯씨」식 호칭이 윗사람에게 실례가 되는 경우가 있다",
        0.86,
        "2026-08-05",
    ),
    ("DE-011", "de", "호칭·경칭", "업무 초반에는 존칭 Sie를 쓰는 편이다", 0.77, "2026-07-30"),
    (
        "PT-011",
        "pt",
        "호칭·경칭",
        "이름 앞 존칭 생략이 어색하게 느껴지는 경우가 있다",
        0.70,
        "2026-07-28",
    ),
    ("KO-031", "ko", "민감 화제", "정치 화제가 초면에 부담스러운 경우가 많다", 0.72, "2026-08-01"),
    (
        "EN-031",
        "en",
        "민감 화제",
        "급여 질문이 사적인 화제로 여겨지는 경우가 많다",
        0.74,
        "2026-08-01",
    ),
    ("JP-031", "ja", "민감 화제", "사적인 질문을 초면에 피하는 편이다", 0.75, "2026-08-01"),
    (
        "DE-031",
        "de",
        "민감 화제",
        "나이·급여 질문이 사적인 화제로 여겨지는 경우가 많다",
        0.72,
        "2026-08-01",
    ),
    ("PT-031", "pt", "민감 화제", "축구 팀 화제가 예상보다 민감한 경우가 있다", 0.68, "2026-08-01"),
    (
        "KO-012",
        "ko",
        "의사 표현",
        "한국어 줄임말은 기계 번역이 실패하는 경우가 많다",
        0.90,
        "2026-08-10",
    ),
]

EVA_TEXT = (
    "에반게리온 팬게임 같이 만들 사람 찾아요. 6주 정도 보고 있고, "
    "유니티 다루는 분과 캐릭터 아트 해주실 분이 필요해요."
)
EVA_ROLES = [
    ("기획 · 디렉팅", 1, 0, "내가 맡아요"),
    ("클라이언트 개발", 1, 1, "Unity · 구하는 중"),
    ("캐릭터 아트", 1, 2, "시트 작업 · 구하는 중"),
]
DELIVERABLES = [
    "기획서 v1.3.pdf",
    "플레이 가능한 빌드.apk",
    "캐릭터 시트 12종.zip",
    "소개 영상.mp4",
]


async def ensure_person(session, spec, password_hash: str) -> Profile:
    key, name, email, locale, city, tz, trust_seed, skills, langs = spec
    user_id = sid(f"user:{key}")
    if await session.get(User, user_id) is None:
        session.add(
            User(id=user_id, email=email, status="ACTIVE", default_locale=locale, token_version=1)
        )
        await session.flush()  # users before password_credentials (no ORM relationships)
        session.add(PasswordCredential(user_id=user_id, password_hash=password_hash))
        await session.flush()
    profile_id = sid(f"profile:{key}")
    profile = await session.get(Profile, profile_id)
    if profile is None:
        profile = Profile(
            id=profile_id,
            kind="PERSON",
            owner_user_id=user_id,
            display_name=name,
            locale=locale,
            timezone=tz,
            city_code=city,
            status="ACTIVE",
        )
        session.add(profile)
        for skill_name, years, verified in skills:
            normalized = skill_name.strip().lower()
            skill = (
                await session.execute(select(Skill).where(Skill.normalized_name == normalized))
            ).scalar_one_or_none()
            if skill is None:
                skill = Skill(
                    id=sid(f"skill:{normalized}"),
                    normalized_name=normalized,
                    display_name=skill_name,
                )
                session.add(skill)
                await session.flush()
            session.add(
                ProfileSkill(
                    profile_id=profile_id,
                    skill_id=skill.id,
                    years_experience=years,
                    verification_status="VERIFIED" if verified else "UNVERIFIED",
                )
            )
        for code, proficiency in langs:
            session.add(
                ProfileLanguage(profile_id=profile_id, language_code=code, proficiency=proficiency)
            )
        for weekday in range(5):
            start, end = (20, 24) if locale == "ko" else (9, 18)
            session.add(
                AvailabilityRule(
                    profile_id=profile_id,
                    weekday=weekday,
                    local_start=time(start, 0),
                    local_end=time(end - 1, 59),
                    timezone=tz,
                    rule_position=weekday,
                )
            )
        if trust_seed:
            session.add(
                TrustEvent(
                    id=sid(f"trust-seed:{key}"),
                    profile_id=profile_id,
                    event_key="DEMO_SEED",
                    demo_delta=trust_seed,
                )
            )
    return profile


async def seed(session, settings) -> None:
    password_hash = PasswordService().hash(PASSWORD)
    people: dict[str, Profile] = {}
    for spec in PEOPLE + FILLERS:
        people[spec[0]] = await ensure_person(session, spec, password_hash)
    await session.flush()

    # Team profile for the BOOKING flow.
    team_id = sid("profile:team-aurora")
    if await session.get(Profile, team_id) is None:
        session.add(
            Profile(
                id=team_id,
                kind="TEAM",
                owner_user_id=None,
                display_name="밴드 아우로라",
                locale="ko",
                timezone="Asia/Seoul",
                city_code="SEOUL",
                status="ACTIVE",
                bio="서울 기반 4인조 시티팝 밴드",
            )
        )

    for kb_id, locale, context, claim, confidence, verified in KB_SEEDS:
        if await session.get(KbNorm, kb_id) is None:
            session.add(
                KbNorm(
                    id=kb_id,
                    claim=claim,
                    scope_locale=locale,
                    scope_context=context,
                    sources=[
                        {
                            "url": f"https://kb.pangaea.dev/{kb_id}/a",
                            "title": "현지 커뮤니티 인터뷰",
                        },
                        {"url": f"https://kb.pangaea.dev/{kb_id}/b", "title": "교차 검증 문헌"},
                    ],
                    verified_at=datetime.strptime(verified, "%Y-%m-%d").date(),
                    confidence=confidence,
                    disputes=[],
                    status="ACTIVE",
                    embedding=pseudo_embedding(kb_id),
                )
            )
    await session.flush()

    # ── EVA fangame WORK signal + crew ───────────────────────────────────────
    eva_id = sid("signal:eva")
    if await session.get(Signal, eva_id) is None:
        parsed = m1.parse(
            EVA_TEXT,
            [
                {"label": label, "headcount": hc, "form_position": pos}
                for label, hc, pos, _ in EVA_ROLES
            ],
        )
        session.add(
            Signal(
                id=eva_id,
                requester_profile_id=people["minseok"].id,
                signal_type="WORK",
                raw_text=EVA_TEXT,
                status="IN_PROGRESS",
                moderation_status="ALLOWED",
                matching_mode="MATCH",
                visibility="PUBLIC",
                source_language="ko",
                urgency="NORMAL",
                requires_physical_presence=False,
                target_is_team=False,
                team_cardinality="1:N",
                headcount_hint=3,
                duration_weeks=6,
                duration_origin="INFERRED",
                compensation_is_paid=True,
                compensation_origin="INFERRED",
                license_risk_flagged=True,
                license_risk_kind="DERIVATIVE_IP",
                license_risk_acknowledged_at=NOW - timedelta(days=42),
                inference_confirmed_at=NOW - timedelta(days=42),
                required_credentials=[],
                policy_snapshot={"parse_schema_version": m1.SCHEMA_VERSION, "disclaimers": []},
                published_at=NOW - timedelta(days=42),
            )
        )
        await session.flush()
        for label, headcount, position, hint in EVA_ROLES:
            session.add(
                SignalRole(
                    id=sid(f"role:eva:{position}"),
                    signal_id=eva_id,
                    label=label,
                    normalized_label=m1.normalize_role_label(label).lower(),
                    headcount=headcount,
                    filled_count=1 if position > 0 else 0,
                    source="USER_FORM",
                    form_position=position,
                    evidence_span=hint,
                )
            )
        for skill in parsed["skills"]:
            session.add(
                SignalSkill(
                    signal_id=eva_id,
                    skill_name=skill["name"],
                    origin=skill["origin"],
                    evidence_span=skill["evidence_span"],
                    confirmation_status="NOT_REQUIRED",
                )
            )
        await session.flush()
        for key, role_position in (("weber", 1), ("sato", 2)):
            session.add(
                Application(
                    id=sid(f"application:eva:{key}"),
                    signal_id=eva_id,
                    applicant_profile_id=people[key].id,
                    role_id=sid(f"role:eva:{role_position}"),
                    direction="INVITATION",
                    message="함께 만들어요!",
                    status="ACCEPTED",
                    decided_at=NOW - timedelta(days=41),
                )
            )

    collab_id = sid("collab:eva")
    collaboration = await session.get(Collaboration, collab_id)
    if collaboration is None:
        collaboration = Collaboration(
            id=collab_id,
            signal_id=eva_id,
            title="EVA 팬게임 크루",
            status="DEPOSIT_PENDING",
            deposit_applies=True,
        )
        session.add(collaboration)
        await session.flush()
        for key, role_label, is_requester in (
            ("minseok", "기획 · 디렉팅", True),
            ("weber", "클라이언트 개발", False),
            ("sato", "캐릭터 아트", False),
        ):
            session.add(
                CollaborationMember(
                    collaboration_id=collab_id,
                    profile_id=people[key].id,
                    role_label=role_label,
                    is_requester=is_requester,
                )
            )
        conversation = Conversation(id=sid("conversation:eva"), collaboration_id=collab_id)
        session.add(conversation)
        await session.flush()

        # Deposit through the real sandbox flow: propose → agree ×3 → fund ×3 → LOCKED.
        agreement = await collab_service.propose_deposit(
            session,
            collaboration,
            acting_profile=people["minseok"],
            amount_minor=100_000,
            clause_keys=["DEPOSIT", "DERIVATIVE_IP", "DELIVERABLE_HASH", "DISSOLUTION"],
            settings=settings,
        )
        for key in ("minseok", "weber", "sato"):
            await collab_service.agree_deposit(session, agreement, profile_id=people[key].id)
        for key in ("minseok", "weber", "sato"):
            await collab_service.fund_deposit(session, agreement, profile_id=people[key].id)

        for position, file_name in enumerate(DELIVERABLES):
            session.add(
                CollaborationDeliverable(
                    id=sid(f"deliverable:eva:{position}"),
                    collaboration_id=collab_id,
                    file_name=file_name,
                    content_hash=uuid.uuid5(NS, f"hash:{file_name}").hex
                    + uuid.uuid5(NS, f"hash2:{file_name}").hex,
                    position=position,
                )
            )

        # The demo chat, through the real orchestration (stub translate/lens/guard).
        members = await chat_service.members_of(session, conversation)
        script = [
            ("weber", "Dieses State-Layer-Design skaliert nicht.", None),
            ("minseok", "상태 관리는 금요일까지 검토해서 알려드릴게요.", None),
            ("sato", "検討させていただきます。", None),
            ("minseok", "그 부분 ㄱㄱ 하시면 될 듯요", "ORIGINAL"),
        ]
        for index, (sender_key, text, guard_choice) in enumerate(script):
            await chat_service.send_message(
                session,
                conversation=conversation,
                members=members,
                sender=people[sender_key],
                client_message_id=f"seed-{index}",
                text=text,
                guard_token=m3.input_hash(text),
                guard_choice=guard_choice,
                settings=settings,
            )

    # ── Kabul HELP (52-second accept) ────────────────────────────────────────
    kabul_id = sid("signal:kabul")
    if await session.get(Signal, kabul_id) is None:
        session.add(
            Signal(
                id=kabul_id,
                requester_profile_id=people["farah"].id,
                signal_type="HELP",
                raw_text="새벽 3시, 카불 — 아이 열이 39도예요. 병원이 어디죠?",
                status="IN_PROGRESS",
                moderation_status="ALLOWED",
                matching_mode="MATCH",
                visibility="PUBLIC",
                source_language="fa",
                urgency="CRITICAL",
                requires_physical_presence=True,
                area_hint="카불",
                target_is_team=False,
                team_cardinality="1:1",
                compensation_is_paid=False,
                compensation_origin="NONE",
                required_credentials=["MEDICAL_LICENSE"],
                policy_snapshot={
                    "disclaimers": [
                        "이 안내는 의료 행위가 아니며 진단·처방을 대체하지 않습니다. "
                        "응급 상황이면 현지 응급번호로 즉시 연락하세요."
                    ]
                },
                published_at=NOW - timedelta(minutes=8),
            )
        )
        await session.flush()
        session.add(
            Application(
                id=sid("application:kabul"),
                signal_id=kabul_id,
                applicant_profile_id=people["nguyen"].id,
                direction="APPLICATION",
                message="근처 병원 알아요.",
                status="ACCEPTED",
                decided_at=NOW - timedelta(minutes=8) + timedelta(seconds=52),
            )
        )

    # ── Retro music CIRCLE (12 participants) ─────────────────────────────────
    circle_id = sid("signal:circle")
    if await session.get(Signal, circle_id) is None:
        session.add(
            Signal(
                id=circle_id,
                requester_profile_id=people["sato"].id,
                signal_type="CIRCLE",
                raw_text="도쿄·서울 — 레트로 게임 음악 감상회, 오늘 밤 9시 온라인. 일본어와 한국어로 대화해요.",
                status="OPEN",
                moderation_status="ALLOWED",
                matching_mode="RECRUITMENT",
                visibility="PUBLIC",
                source_language="ja",
                urgency="NORMAL",
                requires_physical_presence=False,
                target_is_team=False,
                team_cardinality="1:N",
                headcount_hint=20,
                compensation_is_paid=False,
                compensation_origin="NONE",
                required_credentials=[],
                policy_snapshot={"disclaimers": []},
                published_at=NOW - timedelta(hours=5),
            )
        )
        await session.flush()
        participants = ["minseok", "weber", "jkim"] + [f"f{i:02d}" for i in range(1, 10)]
        for index, key in enumerate(participants):
            session.add(
                Application(
                    id=sid(f"application:circle:{key}"),
                    signal_id=circle_id,
                    applicant_profile_id=people[key].id,
                    direction="APPLICATION",
                    status="ACCEPTED",
                    decided_at=NOW - timedelta(hours=4, minutes=index),
                )
            )

    # ── Band festival BOOKING (team target) ──────────────────────────────────
    booking_id = sid("signal:booking")
    if await session.get(Signal, booking_id) is None:
        session.add(
            Signal(
                id=booking_id,
                requester_profile_id=people["jkim"].id,
                signal_type="BOOKING",
                raw_text="10월 홍대 페스티벌 무대에 설 밴드를 찾아요. 시티팝 계열이면 좋겠어요.",
                status="OPEN",
                moderation_status="ALLOWED",
                matching_mode="MATCH",
                visibility="PUBLIC",
                source_language="ko",
                urgency="NORMAL",
                requires_physical_presence=True,
                area_hint="서울",
                target_is_team=True,
                team_cardinality="1:N",
                compensation_is_paid=True,
                compensation_amount_minor=800_000,
                compensation_currency="KRW",
                compensation_origin="EXPLICIT",
                required_credentials=[],
                policy_snapshot={"disclaimers": []},
                published_at=NOW - timedelta(hours=26),
            )
        )

    # A pending application into EVA so the inbox (S09) has a live decision.
    pending_id = sid("application:eva:jkim")
    if await session.get(Application, pending_id) is None:
        session.add(
            Application(
                id=pending_id,
                signal_id=eva_id,
                applicant_profile_id=people["jkim"].id,
                role_id=sid("role:eva:2"),
                direction="APPLICATION",
                message="캐릭터 아트 쪽으로 도울 수 있어요. VFX도 가능합니다.",
                status="PENDING",
            )
        )


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            await seed(session, settings)
            await session.commit()
        print("seed complete — login with e.g. minseok@pangaea.dev /", PASSWORD)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
