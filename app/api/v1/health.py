from collections.abc import Awaitable, Callable

from fastapi import APIRouter

from app.envelope import SuccessEnvelope, ok
from app.errors import ProductError
from app.platform.db import check_database, check_migration_head
from app.platform.redis import check_redis

router = APIRouter(prefix="/health", tags=["health"])


async def component_status(check: Callable[[], Awaitable[None]]) -> str:
    try:
        await check()
    except Exception:
        return "not_ready"
    return "ready"


@router.get("/live", response_model=SuccessEnvelope[dict[str, str]])
async def live() -> SuccessEnvelope[dict[str, str]]:
    return ok({"status": "live"})


@router.get("/ready", response_model=SuccessEnvelope[dict[str, object]])
async def ready() -> SuccessEnvelope[dict[str, object]]:
    components = {
        "database": await component_status(check_database),
        "redis": await component_status(check_redis),
        "migration": await component_status(check_migration_head),
    }
    if any(status != "ready" for status in components.values()):
        raise ProductError(
            code="NOT_READY",
            message="One or more required components are unavailable.",
            status_code=503,
            details={"components": components},
        )

    return ok({"status": "ready", "components": components})
