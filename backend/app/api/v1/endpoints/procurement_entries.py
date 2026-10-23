from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.procurement_entry import (
    ProcurementEntryCreate,
    ProcurementEntryRead,
    ProcurementEntryUpdate,
    ProcurementTransferResult,
)
from app.services import procurement_service as svc

router = APIRouter()


@router.post("", response_model=ProcurementEntryRead, status_code=status.HTTP_201_CREATED)
async def create_procurement_entry(
    payload: ProcurementEntryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:procurement:create"))],
) -> ProcurementEntryRead:
    return await svc.create_entry(db, payload, current)


@router.get("", response_model=PageResponse[ProcurementEntryRead])
async def list_procurement_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:procurement:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    project_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=32),
) -> PageResponse:
    return await svc.list_entries(
        db, page, page_size, q, current_user=current, project_id=project_id, status=status
    )


@router.post("/transfer-arrived", response_model=ProcurementTransferResult)
async def transfer_arrived_procurement(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:procurement:transfer"))],
) -> ProcurementTransferResult:
    return await svc.transfer_arrived_to_actual_cost(db, current)


@router.get("/{entry_id}", response_model=ProcurementEntryRead)
async def get_procurement_entry(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:procurement:read"))],
) -> ProcurementEntryRead:
    return await svc.get_entry_or_404(db, entry_id, current_user=current)


@router.put("/{entry_id}", response_model=ProcurementEntryRead)
async def update_procurement_entry(
    entry_id: UUID,
    payload: ProcurementEntryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:procurement:update"))],
) -> ProcurementEntryRead:
    return await svc.update_entry(db, entry_id, payload, current_user=current)


@router.delete("/{entry_id}", response_model=ProcurementEntryRead)
async def delete_procurement_entry(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:procurement:delete"))],
) -> ProcurementEntryRead:
    return await svc.delete_entry(db, entry_id, current_user=current)


@router.post("/{entry_id}/advance-status", response_model=ProcurementEntryRead)
async def advance_procurement_status(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:procurement:update"))],
) -> ProcurementEntryRead:
    return await svc.advance_entry_status(db, entry_id, current)
