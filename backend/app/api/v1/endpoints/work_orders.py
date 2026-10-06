from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.work_order import (
    WorkOrderChainResult,
    WorkOrderClaim,
    WorkOrderCreate,
    WorkOrderGenerateChain,
    WorkOrderRead,
    WorkOrderSummary,
    WorkOrderUpdate,
)
from app.schemas.accounting import PostExpensePayload
from app.services import work_order_service as svc
from app.services import accounting_service as acct_svc

router = APIRouter()


@router.post("", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    payload: WorkOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:work_order:create"))],
) -> WorkOrderRead:
    return await svc.create_work_order(db, payload, current)


@router.get("/summary", response_model=WorkOrderSummary)
async def get_work_orders_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:work_order:read"))],
) -> WorkOrderSummary:
    return await svc.get_summary(db)


@router.post("/generate-standard-chain", response_model=WorkOrderChainResult)
async def generate_standard_work_order_chain(
    payload: WorkOrderGenerateChain,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:work_order:create"))],
) -> WorkOrderChainResult:
    return await svc.generate_standard_chain(db, payload, current)


@router.get("", response_model=PageResponse)
async def list_work_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:work_order:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    project_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=32),
) -> PageResponse:
    return await svc.list_work_orders(
        db, page, page_size, q, current_user=current, project_id=project_id, status=status
    )


@router.get("/{work_order_id}", response_model=WorkOrderRead)
async def get_work_order(
    work_order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:work_order:read"))],
) -> WorkOrderRead:
    return await svc.get_work_order_or_404(db, work_order_id, current_user=current)


@router.put("/{work_order_id}", response_model=WorkOrderRead)
async def update_work_order(
    work_order_id: UUID,
    payload: WorkOrderUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:work_order:update"))],
) -> WorkOrderRead:
    return await svc.update_work_order(db, work_order_id, payload, current_user=current)


@router.delete("/{work_order_id}", response_model=WorkOrderRead)
async def delete_work_order(
    work_order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:work_order:delete"))],
) -> WorkOrderRead:
    return await svc.delete_work_order(db, work_order_id, current_user=current)


@router.post("/{work_order_id}/advance-status", response_model=WorkOrderRead)
async def advance_work_order_status(
    work_order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:work_order:update"))],
) -> WorkOrderRead:
    return await svc.advance_work_order_status(db, work_order_id)


@router.post("/{work_order_id}/claim", response_model=WorkOrderRead)
async def claim_work_order(
    work_order_id: UUID,
    payload: WorkOrderClaim,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:work_order:update"))],
) -> WorkOrderRead:
    return await svc.claim_work_order(db, work_order_id, payload)


@router.post("/{work_order_id}/post-expense")
async def post_work_order_expense(
    work_order_id: UUID,
    payload: PostExpensePayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:create"))],
):
    return await acct_svc.post_work_order_expense(db, work_order_id, payload, current)
