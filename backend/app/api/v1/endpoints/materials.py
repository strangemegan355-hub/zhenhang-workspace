from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.material import MaterialCreate, MaterialRead, MaterialUpdate
from app.services import material_service as svc

router = APIRouter()


@router.post("", response_model=MaterialRead, status_code=status.HTTP_201_CREATED)
async def create_material(
    payload: MaterialCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:material:create"))],
) -> MaterialRead:
    return await svc.create_material(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse[MaterialRead])
async def list_materials(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:material:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    category_id: UUID | None = Query(default=None),
) -> PageResponse:
    return await svc.list_materials(db, page, page_size, q, category_id)


@router.get("/{material_id}", response_model=MaterialRead)
async def get_material(
    material_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:material:read"))],
) -> MaterialRead:
    return await svc.get_material_or_404(db, material_id)


@router.put("/{material_id}", response_model=MaterialRead)
async def update_material(
    material_id: UUID,
    payload: MaterialUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:material:update"))],
) -> MaterialRead:
    return await svc.update_material(db, material_id, payload.model_dump(exclude_unset=True))


@router.delete("/{material_id}", response_model=MaterialRead)
async def delete_material(
    material_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:material:delete"))],
) -> MaterialRead:
    return await svc.delete_material(db, material_id)
