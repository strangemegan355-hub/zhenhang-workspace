from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.equipment_unit import EquipmentUnitCreate, EquipmentUnitRead, EquipmentUnitUpdate
from app.services import equipment_unit_service as svc
from app.schemas.common import page_response

router = APIRouter()


@router.post("", response_model=EquipmentUnitRead, status_code=status.HTTP_201_CREATED)
async def create_equipment_unit(
    payload: EquipmentUnitCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:equipment_unit:create"))],
) -> dict:
    try:
        return await svc.create_equipment_unit(db, payload.model_dump(), current)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=PageResponse[EquipmentUnitRead])
async def list_equipment_units(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:equipment_unit:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=80),
    build_status: str | None = Query(default=None),
    machine_id: UUID | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
) -> PageResponse:
    items, total = await svc.list_equipment_units(
        db, page, page_size, q, build_status, machine_id, customer_id
    )
    return page_response(total, page, page_size, items, EquipmentUnitRead)


@router.get("/{unit_id}", response_model=EquipmentUnitRead)
async def get_equipment_unit(
    unit_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:equipment_unit:read"))],
) -> dict:
    try:
        return await svc.get_equipment_unit(db, unit_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{unit_id}", response_model=EquipmentUnitRead)
async def update_equipment_unit(
    unit_id: UUID,
    payload: EquipmentUnitUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:equipment_unit:update"))],
) -> dict:
    try:
        return await svc.update_equipment_unit(db, unit_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{unit_id}/advance-status")
async def advance_build_status(
    unit_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:equipment_unit:update"))],
    new_status: str = Query(..., description="Target build status"),
) -> dict:
    try:
        return await svc.advance_build_status(db, unit_id, new_status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
