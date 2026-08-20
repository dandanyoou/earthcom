from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from app.platform.rate_limit import SlidingWindowRateLimiter
from app.settings import get_settings


@pytest.fixture
async def rate_limiter() -> AsyncIterator[SlidingWindowRateLimiter]:
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    namespace = f"test:rate-limit:{uuid4().hex}"
    try:
        yield SlidingWindowRateLimiter(redis, namespace=namespace)
    finally:
        keys = [key async for key in redis.scan_iter(match=f"{namespace}:*")]
        if keys:
            await redis.delete(*keys)
        await redis.aclose()


async def test_same_millisecond_attempts_each_consume_the_sliding_window(
    rate_limiter: SlidingWindowRateLimiter,
) -> None:
    decisions = [
        await rate_limiter.check(
            "peer",
            limit=10,
            window_seconds=600,
            now_ms=1_700_000_000_000,
        )
        for _ in range(11)
    ]

    assert [decision.allowed for decision in decisions] == ([True] * 10) + [False]
    assert decisions[-1].retry_after_seconds == 600


async def test_denied_attempt_is_not_added_and_capacity_returns_at_window_boundary(
    rate_limiter: SlidingWindowRateLimiter,
) -> None:
    first_ms = 1_700_000_000_000
    for offset_ms in range(10):
        decision = await rate_limiter.check(
            "peer",
            limit=10,
            window_seconds=600,
            now_ms=first_ms + offset_ms,
        )
        assert decision.allowed is True

    denied = await rate_limiter.check(
        "peer",
        limit=10,
        window_seconds=600,
        now_ms=first_ms + 10,
    )
    after_window = await rate_limiter.check(
        "peer",
        limit=10,
        window_seconds=600,
        now_ms=first_ms + 600_000,
    )

    assert denied.allowed is False
    assert denied.retry_after_seconds > 0
    assert after_window.allowed is True
