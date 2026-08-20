"""In-app notification list (S11) and read receipts."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.models import Notification
from app.envelope import ok
from app.errors import ProductError
from app.platform.authz import Identity, get_identity
from app.platform.db import get_db_session

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
IdentityDep = Annotated[Identity, Depends(get_identity)]


@router.get("")
async def list_notifications(session: SessionDep, identity: IdentityDep):
    rows = (
        await session.execute(
            select(Notification)
            .where(Notification.user_id == identity.user_id)
            .order_by(Notification.created_at.desc())
            .limit(50)
        )
    ).scalars()
    return ok(
        [
            {
                "id": str(row.id),
                "kind": row.kind,
                "payload": row.payload,
                "resource_type": row.resource_type,
                "resource_id": str(row.resource_id) if row.resource_id else None,
                "read": row.read_at is not None,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    )


@router.post("/{notification_id}/read")
async def mark_read(notification_id: UUID, session: SessionDep, identity: IdentityDep):
    notification = await session.get(Notification, notification_id)
    if notification is None or notification.user_id != identity.user_id:
        raise ProductError(
            code="NOTIFICATION_NOT_FOUND", message="notification not found", status_code=404
        )
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
        await session.commit()
    return ok({"id": str(notification.id), "read": True})
