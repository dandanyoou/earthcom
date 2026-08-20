"""Culture KB evidence sheet (S04a) and the "we don't do that" dispute inlet.

Disputes genuinely lower effective confidence (§9.6) — the endpoint appends to
the record's dispute list, and the decay math picks it up immediately.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.domains.kb.models import KbNorm
from app.envelope import ok
from app.errors import ProductError
from app.platform.authz import Identity, get_identity
from app.platform.db import get_db_session
from pangaea_ai.gates import confidence_level, effective_confidence

router = APIRouter(prefix="/api/v1/kb", tags=["kb"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
IdentityDep = Annotated[Identity, Depends(get_identity)]


class DisputeInput(BaseModel):
    comment: str = Field(min_length=1, max_length=300)


def _payload(record: KbNorm) -> dict:
    today = datetime.now(UTC).date()
    effective = effective_confidence(
        float(record.confidence), record.verified_at, len(record.disputes or []), today=today
    )
    return {
        "id": record.id,
        "claim": record.claim,
        "scope_locale": record.scope_locale,
        "scope_context": record.scope_context,
        "sources": record.sources,
        "verified_at": record.verified_at.isoformat(),
        "base_confidence": float(record.confidence),
        "effective_confidence": effective,
        "level": confidence_level(effective),
        "dispute_count": len(record.disputes or []),
        "status": record.status,
    }


@router.get("/{kb_id}")
async def kb_detail(kb_id: str, session: SessionDep, identity: IdentityDep):
    record = await session.get(KbNorm, kb_id)
    if record is None or record.status != "ACTIVE":
        raise ProductError(code="KB_NOT_FOUND", message="record not found", status_code=404)
    return ok(_payload(record))


@router.post("/{kb_id}/disputes", status_code=201)
async def add_dispute(kb_id: str, body: DisputeInput, session: SessionDep, identity: IdentityDep):
    record = await session.get(KbNorm, kb_id)
    if record is None or record.status != "ACTIVE":
        raise ProductError(code="KB_NOT_FOUND", message="record not found", status_code=404)
    disputes = list(record.disputes or [])
    disputes.append(
        {
            "comment": body.comment,
            "profile_id": str(identity.profile_id) if identity.profile_id else None,
            "at": datetime.now(UTC).isoformat(),
        }
    )
    record.disputes = disputes
    flag_modified(record, "disputes")
    await session.commit()
    return ok(_payload(record))
