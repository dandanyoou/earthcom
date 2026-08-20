"""End-to-end demo slice over the HTTP surface, on a freshly seeded database."""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.settings import get_settings
from scripts.seed_demo import PASSWORD, seed


async def seed_database() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            await seed(session, settings)
            await session.commit()
    finally:
        await engine.dispose()


async def login(client, email: str) -> dict:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_demo_slice_end_to_end(auth_environment) -> None:
    client = auth_environment.client
    await seed_database()
    minseok = await login(client, "minseok@pangaea.dev")

    # ── Home: seeded trust temperature and the 52-second Kabul accept ────────
    home = (await client.get("/api/v1/home", headers=minseok)).json()["data"]
    assert home["profile"]["trust"]["value"] == 37.3
    assert home["profile"]["trust"]["is_demo"] is True
    kabul = next(s for s in home["signals"] if s["signal_type"] == "HELP")
    assert kabul["accept_latency_seconds"] == 52
    circle = next(s for s in home["signals"] if s["signal_type"] == "CIRCLE")
    assert circle["accepted_count"] == 12

    # ── Parse preview: dashed estimates, roles passed through verbatim ───────
    parse = (
        await client.post(
            "/api/v1/ai/parse",
            headers=minseok,
            json={
                "raw_text": "유니티 셰이더 이펙트 도와줄 분 찾아요. 3주 정도 생각 중이에요.",
                "roles_form": [{"label": "셰이더 개발", "headcount": 1, "form_position": 0}],
            },
        )
    ).json()
    assert parse["ok"] is True
    assert parse["data"]["duration"] == {
        "weeks": 3,
        "origin": "INFERRED",
        "evidence_span": "3주",
    }
    assert [r["label"] for r in parse["data"]["roles_requested"]] == ["셰이더 개발"]

    # ── Create + publish gate: estimates must be confirmed first ─────────────
    created = (
        await client.post(
            "/api/v1/signals",
            headers=minseok,
            json={
                "raw_text": "유니티 셰이더 이펙트 도와줄 분 찾아요. 3주 정도 생각 중이에요.",
                "roles_form": [{"label": "셰이더 개발", "headcount": 1, "form_position": 0}],
            },
        )
    ).json()["data"]
    signal_id = created["id"]
    blocked = await client.post(f"/api/v1/signals/{signal_id}/publish", headers=minseok, json={})
    assert blocked.status_code == 422
    assert blocked.json()["error"]["code"] == "SIGNAL_INFERENCE_CONFIRMATION_REQUIRED"
    published = await client.post(
        f"/api/v1/signals/{signal_id}/publish",
        headers=minseok,
        json={"inferred_confirmed": True},
    )
    assert published.status_code == 200
    assert published.json()["data"]["status"] == "OPEN"

    # ── Recommendations: lexicographic order, server-owned explain panel ─────
    recommendations = (
        await client.get(f"/api/v1/signals/{signal_id}/recommendations", headers=minseok)
    ).json()["data"]
    assert recommendations["explain"]["policy_version"] == "matching.v1"
    assert "cultureExcluded" in recommendations["explain"]["exclusions"]
    top = recommendations["candidates"][0]
    assert top["profile"]["display_name"] == "L. Weber"
    assert top["role_fit"] == "MATCHED"
    assert top["why"]  # M6 sentence, numbers only from server facts

    # ── Direct search through M8 expansion ───────────────────────────────────
    search = (
        await client.get(
            "/api/v1/search/profiles",
            headers=minseok,
            params={"q": "유니티 셰이더 잘하는 사람"},
        )
    ).json()["data"]
    assert search["results"][0]["display_name"] == "L. Weber"
    assert any(term.lower() == "unity" for term in search["terms"])

    # ── Chat: guard freshness contract, slang ships as original + chip ───────
    collaborations = (await client.get("/api/v1/collaborations", headers=minseok)).json()["data"]
    eva = next(c for c in collaborations if c["title"] == "EVA 팬게임 크루")
    conversation_id = eva["conversation_id"]
    assert eva["deposit"]["status"] == "LOCKED"

    guard = (
        await client.post(
            "/api/v1/ai/guard",
            headers=minseok,
            json={"conversation_id": conversation_id, "text": "Sato씨, 시트 봤어요!"},
        )
    ).json()
    assert guard["data"]["display"] is True
    assert guard["data"]["kb_ids"] == ["JP-011"]

    stale = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=minseok,
        json={"client_message_id": "t-1", "text": "Sato씨, 시트 봤어요!"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "MESSAGE_GUARD_STALE"
    sent = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=minseok,
        json={
            "client_message_id": "t-1",
            "text": "Sato씨, 시트 봤어요!",
            "guard_token": stale.json()["error"]["details"]["guard_token"],
            "guard_choice": "ORIGINAL",
        },
    )
    assert sent.status_code == 201
    assert sent.json()["data"]["guard_badge"] == "SENT_UNCHANGED"
    assert sent.json()["data"]["translation_status"] == "REVIEW_REQUIRED"

    # Seeded history renders translations + culture help for the viewer.
    messages = (
        await client.get(f"/api/v1/conversations/{conversation_id}/messages", headers=minseok)
    ).json()["data"]
    weber_message = next(m for m in messages if m["sender"]["name"] == "L. Weber")
    assert weber_message["shown_text"].startswith("이 상태 관리 구조는")
    assert weber_message["original_line"] == "Dieses State-Layer-Design skaliert nicht."
    assert weber_message["help"]["kb_ids"] == ["DE-014"]
    sato_message = next(m for m in messages if m["sender"]["name"] == "M. Sato")
    assert sato_message["help"]["kb_ids"] == ["JP-007"]

    # ── IDOR: a non-member cannot read the crew conversation ─────────────────
    costa = await login(client, "costa@pangaea.dev")
    denied = await client.get(f"/api/v1/conversations/{conversation_id}/messages", headers=costa)
    assert denied.status_code == 403

    # ── Completion: everyone confirms → refund → +1.2 for each member ────────
    weber = await login(client, "weber@pangaea.dev")
    sato = await login(client, "sato@pangaea.dev")
    for headers in (minseok, weber, sato):
        done = await client.post(
            f"/api/v1/collaborations/{eva['id']}/completion-confirmations",
            headers=headers,
        )
        assert done.status_code == 200
    final = done.json()["data"]
    assert final["completed"] is True
    collaboration = final["collaboration"]
    assert collaboration["status"] == "COMPLETED"
    assert collaboration["deposit"]["status"] == "REFUNDED"
    assert all(p["refunded"] for p in collaboration["deposit"]["parties"])
    trust_by_name = {m["name"]: m["trust"]["value"] for m in collaboration["members"]}
    assert trust_by_name["이민석"] == 38.5  # 37.3 + 1.2, exactly the mockup
    assert trust_by_name["L. Weber"] == 42.4

    # A completed collaboration rejects further confirmations, and trust
    # events were appended exactly once per member.
    again = await client.post(
        f"/api/v1/collaborations/{eva['id']}/completion-confirmations", headers=minseok
    )
    assert again.status_code == 409
    minseok_id = next(m["profile_id"] for m in collaboration["members"] if m["name"] == "이민석")
    trust = (await client.get(f"/api/v1/profiles/{minseok_id}/trust", headers=minseok)).json()[
        "data"
    ]
    assert trust["value"] == 38.5

    # ── Review: +0.3 for a positive rating, once per pair ────────────────────
    weber_id = next(m["profile_id"] for m in collaboration["members"] if m["name"] == "L. Weber")
    review = await client.post(
        f"/api/v1/collaborations/{eva['id']}/reviews",
        headers=minseok,
        json={"reviewee_profile_id": weber_id, "rating": "POSITIVE", "tags": ["기한 준수"]},
    )
    assert review.status_code == 201
    weber_trust = (await client.get(f"/api/v1/profiles/{weber_id}/trust", headers=minseok)).json()[
        "data"
    ]
    assert weber_trust["value"] == 42.7


async def test_signal_moderation_and_pii_gate(auth_environment) -> None:
    client = auth_environment.client
    await seed_database()
    minseok = await login(client, "minseok@pangaea.dev")

    # Self-harm text never reaches the parser; the envelope degrades to a notice.
    crisis = (
        await client.post(
            "/api/v1/ai/parse",
            headers=minseok,
            json={"raw_text": "요즘 죽고 싶다는 생각이 들어요", "roles_form": []},
        )
    ).json()
    assert crisis["degraded"] is True
    assert crisis["degrade_reason"] == "MODERATION"
    assert "crisis_notice" in crisis["data"]

    # Contact details block publication (PII lint).
    created = (
        await client.post(
            "/api/v1/signals",
            headers=minseok,
            json={"raw_text": "리액트 도와줄 분 010-1234-5678로 연락주세요", "roles_form": []},
        )
    ).json()["data"]
    blocked = await client.post(
        f"/api/v1/signals/{created['id']}/publish",
        headers=minseok,
        json={"inferred_confirmed": True},
    )
    assert blocked.status_code == 422
    assert blocked.json()["error"]["code"] == "SIGNAL_PII_PRESENT"
