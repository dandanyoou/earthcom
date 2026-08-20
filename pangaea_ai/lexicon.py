"""Deterministic dictionaries behind stub mode.

Everything the demo needs works from these tables with zero network calls.
They are expression aids only — nothing here scores, ranks, or judges.
"""

# ── Skills ────────────────────────────────────────────────────────────────────
# canonical name → aliases found in free text (lowercase match).
SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Unity": ("unity", "유니티"),
    "셰이더": ("셰이더", "쉐이더", "shader"),
    "캐릭터 아트": ("캐릭터 아트", "캐릭터아트", "원화", "일러스트", "character art"),
    "게임 기획": ("게임 기획", "기획", "디렉팅", "game design"),
    "사운드": ("사운드", "작곡", "음향", "sound", "bgm"),
    "React": ("react", "리액트"),
    "Python": ("python", "파이썬"),
    "영상 편집": ("영상 편집", "영상편집", "편집자", "video editing"),
    "번역": ("번역", "translation"),
    "통역": ("통역", "interpreter"),
    "VFX": ("vfx", "이펙트"),
    "최적화": ("최적화", "optimization"),
    "툴 개발": ("툴 개발", "툴개발", "tooling"),
    "보컬": ("보컬", "vocal"),
    "기타": ("기타리스트", "guitar"),
    "드럼": ("드럼", "drum"),
}

# search normalization: term → expansion set (M8 widens the query, never ranks).
SEARCH_SYNONYMS: dict[str, tuple[str, ...]] = {
    "유니티": ("unity",),
    "unity": ("유니티",),
    "셰이더": ("shader", "쉐이더"),
    "shader": ("셰이더",),
    "밴드": ("band", "バンド"),
    "band": ("밴드", "バンド"),
    "그림": ("일러스트", "캐릭터 아트", "illustration"),
    "일러스트": ("캐릭터 아트", "illustration"),
    "번역": ("translation",),
    "사운드": ("sound", "작곡"),
    "react": ("리액트",),
    "파이썬": ("python",),
}

CITY_NAMES: dict[str, str] = {
    "서울": "SEOUL",
    "베를린": "BERLIN",
    "도쿄": "TOKYO",
    "리스본": "LISBON",
    "뉴욕": "NEW_YORK",
    "카불": "KABUL",
    "하노이": "HANOI",
    "크라쿠프": "KRAKOW",
    "멕시코시티": "MEXICO_CITY",
}

# ── Parse heuristics ─────────────────────────────────────────────────────────
SIGNAL_TYPE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("HELP", ("도와", "도움", "급해", "응급", "병원", "부탁", "찾아주세", "help")),
    ("BOOKING", ("섭외", "공연", "출연", "무대", "페스티벌", "행사에", "booking")),
    ("CIRCLE", ("모임", "감상회", "스터디", "같이 들", "동호회", "번개", "meetup")),
    ("WORK", ("만들", "개발", "구인", "구합", "프로젝트", "작업할", "의뢰", "채용")),
)
URGENCY_CRITICAL = ("응급", "위급", "새벽인데", "지금 당장", "emergency")
URGENCY_HIGH = ("급해", "급하게", "오늘 안에", "asap", "빨리")
DERIVATIVE_IP_KEYWORDS = (
    "팬게임",
    "팬 게임",
    "2차 창작",
    "2차창작",
    "팬아트",
    "원작",
    "에반게리온",
    "fangame",
)
CREDENTIAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "MEDICAL_LICENSE": ("병원", "의사", "간호", "의료", "진료"),
    "LEGAL_LICENSE": ("법률", "변호사", "계약서 검토"),
    "INTERPRETER": ("통역",),
    "DRIVER_LICENSE": ("운전", "차로 데려다"),
}
PHYSICAL_PRESENCE_KEYWORDS = ("현장", "방문", "직접 와", "대면", "오프라인", "와 주실", "와주실")
HEDGE_MARKERS = ("정도", "쯤", "약 ", "가량", "내외", "생각 중", "보고 있")
UNPAID_MARKERS = ("무보수", "보수 없", "무료로", "재능 기부", "재능기부")
TEAM_TARGET_MARKERS = ("밴드", "팀을 찾", "팀 단위", "그룹을")

# ── Moderation (pre-processing, deterministic) ───────────────────────────────
SELF_HARM_MARKERS = ("자살", "자해", "죽고 싶", "죽고싶", "삶을 끝내")
CRISIS_GUIDANCE_KEY = "SELF_HARM_ROUTE"

# High-risk deterministic disclaimers — constants, never model output (§9.5).
DISCLAIMERS = {
    "MEDICAL": (
        "이 안내는 의료 행위가 아니며 진단·처방을 대체하지 않습니다. "
        "응급 상황이면 현지 응급번호로 즉시 연락하세요."
    ),
    "LEGAL": "이 안내는 법률 자문이 아닙니다.",
}

# ── Guard lexicon (M3) ───────────────────────────────────────────────────────
# Each rule: pattern(str, lowercase contains) or regex marker, phenomenon,
# risk, target language spheres it applies to, kb id, reader reading,
# suggestion template ({{honorific}} style slots stay deterministic).
GUARD_RULES: tuple[dict, ...] = (
    {
        "id": "honorific-ssi",
        "regex": r"(?:[A-Z][a-zA-Z]+|사토|사또)\s*씨",
        "phenomenon": "HONORIFIC_MISMATCH",
        "risk": "HIGH",
        "target_langs": ("ja",),
        "kb_ids": ("JP-011",),
        "reader_reading": "윗사람에게 쓰면 가볍게 들릴 수 있는 호칭이에요.",
        "suggestion": "「◯◯さん」 또는 「◯◯ 작가님」처럼 상대를 높이는 호칭으로 바꿔보세요.",
        "rewrite": ("regex", r"([A-Za-z]+|사토|사또)\s*씨", r"\1さん"),
        "confidence": 0.86,
    },
    {
        "id": "slang-abbrev",
        "regex": r"(?:ㄱㄱ|ㄴㄴ|ㅇㅋ|ㅊㅋ|ㄹㅇ|ㅇㅇ)",
        "phenomenon": "UNTRANSLATABLE_IDIOM",
        "risk": "MEDIUM",
        "target_langs": ("ja", "de", "en", "pt"),
        "kb_ids": ("KO-012",),
        "reader_reading": "한국어 줄임말은 기계 번역이 자주 실패해요.",
        "suggestion": "줄임말을 풀어 쓰면 번역이 훨씬 정확해져요. 예: 「진행해 주세요」.",
        "rewrite": (
            "dict",
            {
                "ㄱㄱ": "진행",
                "ㄴㄴ": "아니요",
                "ㅇㅋ": "알겠어요",
                "ㅊㅋ": "축하해요",
                "ㄹㅇ": "정말",
                "ㅇㅇ": "네",
            },
        ),
        "confidence": 0.9,
    },
    {
        "id": "euphemistic-hold",
        "regex": r"(?:검토해\s*보겠|검토하겠|생각해\s*보겠|고민해\s*보겠)",
        "phenomenon": "EUPHEMISTIC_REFUSAL",
        "risk": "MEDIUM",
        "target_langs": ("de", "en"),
        "kb_ids": ("KO-001",),
        "reader_reading": "직설 문화권 상대는 곧 답이 온다고 기대할 수 있어요.",
        "suggestion": (
            "보류라면 「지금은 어렵고, [기한]까지 답드릴게요」처럼 상태를 분명히 해보세요."
        ),
        "confidence": 0.78,
    },
    {
        "id": "vague-deadline",
        "regex": r"(?:나중에|언젠가|조만간|시간 될 때)",
        "phenomenon": "VAGUE_DEADLINE",
        "risk": "MEDIUM",
        "target_langs": ("de",),
        "kb_ids": ("DE-021",),
        "reader_reading": "독일어권에서는 기한 없는 약속이 무성의로 읽히는 경우가 있어요.",
        "suggestion": "「[기한]까지」처럼 날짜를 함께 적어보세요. 날짜는 직접 정해 주세요.",
        "confidence": 0.74,
    },
    {
        "id": "taboo-age-salary",
        "regex": r"(?:나이가 어떻게|몇 살|연봉이|월급이)",
        "phenomenon": "TABOO_TOPIC",
        "risk": "LOW",
        "target_langs": ("de", "en", "ja"),
        "kb_ids": ("DE-031",),
        "reader_reading": "처음 협업하는 사이에는 사적인 화제로 느껴질 수 있어요.",
        "suggestion": (
            "작업 조건이 궁금하다면 「가능한 작업 시간대」처럼 일 중심으로 물어보세요. "
            "상대에 따라 다를 수 있어요."
        ),
        "confidence": 0.72,
    },
)

# ── Translation fixtures (stub provider) ─────────────────────────────────────
# Normalized source text → {target_lang: translated}. Mirrors the demo chat.
TRANSLATION_FIXTURES: dict[str, dict[str, str]] = {
    "Dieses State-Layer-Design skaliert nicht.": {
        "ko": "이 상태 관리 구조는 확장이 안 됩니다. 다시 만드는 게 맞습니다.",
        "en": "This state layer design does not scale. It should be rebuilt.",
    },
    "상태 관리는 금요일까지 검토해서 알려드릴게요.": {
        "de": "Ich schaue mir das State-Management an und melde mich bis Freitag.",
        "ja": "状態管理は金曜日までに確認してお知らせします。",
        "en": "I will review the state management and get back to you by Friday.",
    },
    "検討させていただきます。": {
        "ko": "검토해 보겠습니다.",
        "en": "I will consider it.",
    },
    "안녕하세요! 잘 부탁드립니다.": {
        "de": "Hallo! Ich freue mich auf die Zusammenarbeit.",
        "ja": "こんにちは！よろしくお願いします。",
        "en": "Hello! Looking forward to working with you.",
    },
    "고생 많으셨어요. 다음 주에 봬요.": {
        "de": "Gute Arbeit heute. Bis nächste Woche!",
        "ja": "お疲れさまでした。また来週お会いしましょう。",
        "en": "Great work today. See you next week!",
    },
    "빌드는 3일 안에 공유드릴게요.": {
        "de": "Ich teile den Build innerhalb von 3 Tagen.",
        "ja": "ビルドは3日以内に共有します。",
        "en": "I will share the build within 3 days.",
    },
}

# ── Lens (M2) keyword → KB matching, per language sphere ─────────────────────
LENS_TRIGGERS: tuple[dict, ...] = (
    {
        "source_langs": ("de",),
        "regex": r"(?:skaliert nicht|funktioniert nicht|안 됩니다|다시 만드는)",
        "kb_id": "DE-014",
        "heading": "READ_AS",  # 「이렇게 읽으시면 좋아요」
        "annotation": (
            "독일어권에서는 일 이야기를 직설적으로 하는 편이에요. 비난이 아닐 가능성이 높아요."
        ),
    },
    {
        "source_langs": ("ja",),
        "regex": r"(?:検討|검토해 보겠습니다)",
        "kb_id": "JP-007",
        "heading": "MAY_MEAN",  # 「이런 뜻일 수 있어요」
        "annotation": "정중한 보류가 사실상 거절인 경우가 있어요. 다른 방법을 제안해 보세요.",
    },
    {
        "source_langs": ("pt",),
        "regex": r"(?:tudo bem|como vai|가족|주말 어땠)",
        "kb_id": "PT-003",
        "heading": "READ_AS",
        "annotation": (
            "포르투갈어권에서는 스몰토크가 신뢰 형성에 중요한 편이에요. "
            "바로 본론으로 가지 않아도 괜찮아요."
        ),
    },
)

# ── Why (M6) sentence skeletons — numbers only ever appear as slots ──────────
WHY_TEMPLATES: tuple[dict, ...] = (
    {
        "requires": ("skill", "years"),
        "template": "{{skill}} 경력 {{years}}년이라 찾으시는 기술과 바로 이어져요.",
    },
    {
        "requires": ("skill", "overlap_hours"),
        "template": (
            "{{skill}}{{skill:을/를}} 다루고, "
            "겹치는 시간이 하루 {{overlap_hours}}시간이라 소통이 수월해요."
        ),
    },
    {
        "requires": ("verified_count",),
        "template": "끝까지 마친 작업 {{verified_count}}건이 결과물로 확인됐어요.",
    },
    {
        "requires": ("skill",),
        "template": "{{skill}} 작업을 해 온 분이라 요청 내용과 결이 맞아요.",
    },
)

# ── Deposit clause templates (M7) — amounts are slots, never model output ────
DEPOSIT_CLAUSES: dict[str, str] = {
    "DEPOSIT": "참여자 전원이 약속 보증금 {{amount}}을 맡기고, 약속을 지키면 전액 돌려받아요.",
    "DERIVATIVE_IP": "원작 IP를 쓰는 작업은 비상업 조건인지 함께 확인하기로 해요.",
    "ASYNC_COLLAB": "시차가 있는 크루라서, 답장은 겹치는 시간 기준 하루 안에 하기로 해요.",
    "DELIVERABLE_HASH": "결과물은 파일 지문(해시)과 함께 남겨 서로의 기여를 증명해요.",
    "DISSOLUTION": "작업이 끝나면 크루는 해산하고, 기록과 결과물만 남아요.",
}
DEPOSIT_NOTICE = "보증금은 작업 대금이 아닙니다. 대금 지급 방법은 당사자끼리 따로 정해야 합니다."
