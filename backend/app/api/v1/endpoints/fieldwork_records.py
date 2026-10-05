from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.accounting import AccountingEntryRead
from app.schemas.common import PageResponse
from app.schemas.fieldwork_record import (
    FieldworkRecordCreate,
    FieldworkRecordRead,
    FieldworkRecordUpdate,
    FieldworkSummary,
)
from app.schemas.accounting import AccountingEntryRead
from app.services import fieldwork_receivable_service as fwr_svc
from app.services import fieldwork_service as svc

router = APIRouter()


@router.post("", response_model=FieldworkRecordRead, status_code=status.HTTP_201_CREATED)
async def create_fieldwork_record(
    payload: FieldworkRecordCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:fieldwork:create"))],
) -> FieldworkRecordRead:
    return await svc.create_record(db, payload, current)


@router.get("/summary", response_model=FieldworkSummary)
async def get_fieldwork_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:fieldwork:read"))],
) -> FieldworkSummary:
    return await svc.get_summary(db)


@router.get("", response_model=PageResponse)
async def list_fieldwork_records(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:fieldwork:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    record_type: str | None = Query(default=None, max_length=32),
    status: str | None = Query(default=None, max_length=32),
    project_id: UUID | None = Query(default=None),
) -> PageResponse:
    return await svc.list_records(
        db,
        page,
        page_size,
        q,
        current_user=current,
        record_type=record_type,
        status=status,
        project_id=project_id,
    )


@router.get("/{record_id}", response_model=FieldworkRecordRead)
async def get_fieldwork_record(
    record_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:fieldwork:read"))],
) -> FieldworkRecordRead:
    return await svc.get_record_or_404(db, record_id, current_user=current)


@router.put("/{record_id}", response_model=FieldworkRecordRead)
async def update_fieldwork_record(
    record_id: UUID,
    payload: FieldworkRecordUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:fieldwork:update"))],
) -> FieldworkRecordRead:
    return await svc.update_record(db, record_id, payload, current_user=current)


@router.delete("/{record_id}", response_model=FieldworkRecordRead)
async def delete_fieldwork_record(
    record_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:fieldwork:delete"))],
) -> FieldworkRecordRead:
    return await svc.delete_record(db, record_id, current_user=current)


@router.post("/{record_id}/advance-status", response_model=FieldworkRecordRead)
async def advance_fieldwork_status(
    record_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:fieldwork:update"))],
) -> FieldworkRecordRead:
    return await svc.advance_record_status(db, record_id)


@router.post("/{record_id}/post-receivable", response_model=AccountingEntryRead)
async def post_fieldwork_repair_receivable(
    record_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:create"))],
) -> AccountingEntryRead:
    return await fwr_svc.post_receivable_from_repair(db, record_id, current)
