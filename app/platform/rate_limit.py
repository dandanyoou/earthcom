from dataclasses import dataclass
from uuid import uuid4

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.errors import ProductError

SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, '-inf', now_ms - window_ms)
local count = redis.call('ZCARD', key)
if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_ms = tonumber(oldest[2]) + window_ms - now_ms
    local retry_seconds = math.max(1, math.ceil(retry_ms / 1000))
    return {0, retry_seconds}
end

redis.call('ZADD', key, now_ms, member)
redis.call('PEXPIRE', key, window_ms)
return {1, 0}
"""


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class SlidingWindowRateLimiter:
    def __init__(self, redis: Redis, *, namespace: str = "pangaea:rate-limit") -> None:
        self._redis = redis
        self._namespace = namespace

    async def check(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
        now_ms: int,
    ) -> RateLimitDecision:
        window_ms = window_seconds * 1000
        member = f"{now_ms}:{uuid4().hex}"
        try:
            result = await self._redis.eval(
                SLIDING_WINDOW_SCRIPT,
                1,
                f"{self._namespace}:{key}",
                now_ms,
                window_ms,
                limit,
                member,
            )
        except RedisError:
            raise ProductError(
                code="DEPENDENCY_UNAVAILABLE",
                message="A required dependency is unavailable.",
                status_code=503,
            ) from None

        return RateLimitDecision(
            allowed=bool(result[0]),
            retry_after_seconds=int(result[1]),
        )
