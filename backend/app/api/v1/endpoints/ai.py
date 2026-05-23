from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.domains.quote.application import quote_application_service as quote_svc
from app.models.user import User

router = APIRouter()


@router.get("/copilot/quote-summary")
async def copilot_quote_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:quote:read"))],
    quote_id: UUID = Query(...),
    from_version_no: int | None = Query(default=None, ge=1),
    to_version_no: int | None = Query(default=None, ge=1),
) -> dict:
    return await quote_svc.summarize_quote_for_copilot(
        db, quote_id, from_version_no=from_version_no, to_version_no=to_version_no
    )
