from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_any_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.approval_hub import ApprovalActionPayload, ApprovalInboxResponse
from app.services import approval_hub_service as svc

router = APIRouter()


@router.get("/inbox", response_model=ApprovalInboxResponse)
async def get_approval_inbox(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[
        User,
        Depends(require_any_permission("business:quote:approve", "business:accounting:approve_quote_receivable")),
    ],
) -> ApprovalInboxResponse:
    return await svc.list_inbox(db, current)


@router.post("/action")
async def execute_approval_action(
    payload: ApprovalActionPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[
        User,
        Depends(require_any_permission("business:quote:approve", "business:accounting:approve_quote_receivable")),
    ],
) -> dict:
    return await svc.execute_action(
        db,
        task_type=payload.task_type,
        task_id=payload.task_id,
        action=payload.action,
        comment=payload.comment,
        current_user=current,
    )
