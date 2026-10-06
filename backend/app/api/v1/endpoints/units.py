from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.unit import UnitCreate, UnitRead, UnitUpdate
from app.services import unit_service as svc

router = APIRouter()


@router.post("", response_model=UnitRead, status_code=status.HTTP_201_CREATED)
async def create_unit(
    payload: UnitCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:standard:create"))],
) -> UnitRead:
    return await svc.create_unit(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse[UnitRead])
async def list_units(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:standard:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_units(db, page, page_size, q)


@router.get("/{unit_id}", response_model=UnitRead)
async def get_unit(
    unit_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:standard:read"))],
) -> UnitRead:
    return await svc.get_unit_or_404(db, unit_id)


@router.put("/{unit_id}", response_model=UnitRead)
async def update_unit(
    unit_id: UUID,
    payload: UnitUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:standard:update"))],
) -> UnitRead:
    return await svc.update_unit(db, unit_id, payload.model_dump(exclude_unset=True))


@router.delete("/{unit_id}", response_model=UnitRead)
async def delete_unit(
    unit_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:standard:delete"))],
) -> UnitRead:
    return await svc.delete_unit(db, unit_id)
