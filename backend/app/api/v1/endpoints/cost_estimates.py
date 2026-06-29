from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.accounting import PostExpensePayload
from app.schemas.common import PageResponse
from app.schemas.cost_estimate import (
    CostEstimateCreate,
    CostEstimatePreviewRequest,
    CostEstimatePreviewResponse,
    CostEstimateRead,
    CostEstimateUpdate,
)
from app.services import costing_service as svc
from app.services import accounting_service as acct_svc

router = APIRouter()


@router.post("/preview", response_model=CostEstimatePreviewResponse)
async def preview_cost_estimate(
    payload: CostEstimatePreviewRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:cost_estimate:read"))],
) -> CostEstimatePreviewResponse:
    return await svc.preview_cost_estimate(db, payload)


@router.post("", response_model=CostEstimateRead, status_code=status.HTTP_201_CREATED)
async def create_cost_estimate(
    payload: CostEstimateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:cost_estimate:create"))],
) -> CostEstimateRead:
    return await svc.create_cost_estimate(db, payload, current)


@router.get("", response_model=PageResponse)
async def list_cost_estimates(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:cost_estimate:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_cost_estimates(db, page, page_size, q)


@router.get("/{estimate_id}", response_model=CostEstimateRead)
async def get_cost_estimate(
    estimate_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:cost_estimate:read"))],
) -> CostEstimateRead:
    return await svc.get_cost_estimate_or_404(db, estimate_id)


@router.put("/{estimate_id}", response_model=CostEstimateRead)
async def update_cost_estimate(
    estimate_id: UUID,
    payload: CostEstimateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:cost_estimate:update"))],
) -> CostEstimateRead:
    return await svc.update_cost_estimate(db, estimate_id, payload)


@router.delete("/{estimate_id}", response_model=CostEstimateRead)
async def delete_cost_estimate(
    estimate_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:cost_estimate:delete"))],
) -> CostEstimateRead:
    return await svc.delete_cost_estimate(db, estimate_id)


@router.post("/{estimate_id}/post-expense")
async def post_cost_estimate_expense(
    estimate_id: UUID,
    payload: PostExpensePayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:create"))],
):
    await acct_svc.require_accounting_enabled(db)
    from app.repositories import accounting_repository as repo, cost_estimate_repository as est_repo
    est = await est_repo.get_cost_estimate(db, estimate_id)
    if est is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Cost estimate not found")
    obj = await repo.create_entry(db, {
        "entry_no": await repo.generate_entry_no(db, "expense"),
        "entry_kind": "expense",
        "status": "confirmed",
        "party_type": None,
        "customer_id": None,
        "supplier_id": None,
        "project_id": None,
        "amount": float(payload.amount),
        "settled_amount": 0,
        "currency": "CNY",
        "occurred_on": date.today(),
        "due_date": None,
        "booked_on": date.today(),
        "is_backfill": False,
        "source_type": "cost_estimate",
        "source_id": estimate_id,
        "source_no": est.estimate_no,
        "approval_status": "none",
        "title": payload.title.strip(),
        "remark": payload.remark.strip() if payload.remark else None,
        "created_by": current.id,
    })
    loaded = await repo.get_entry(db, obj.id)
    from app.schemas.accounting import AccountingEntryRead
    return AccountingEntryRead.model_validate(loaded or obj)
