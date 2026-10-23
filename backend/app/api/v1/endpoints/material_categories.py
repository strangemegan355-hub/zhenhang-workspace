from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.material_category import (
    MaterialCategoryCreate,
    MaterialCategoryRead,
    MaterialCategoryUpdate,
)
from app.services import material_category_service as svc

router = APIRouter()


@router.post("", response_model=MaterialCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_material_category(
    payload: MaterialCategoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:standard:create"))],
) -> MaterialCategoryRead:
    return await svc.create_material_category(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse[MaterialCategoryRead])
async def list_material_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:standard:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_material_categories(db, page, page_size, q)


@router.get("/{category_id}", response_model=MaterialCategoryRead)
async def get_material_category(
    category_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:standard:read"))],
) -> MaterialCategoryRead:
    return await svc.get_material_category_or_404(db, category_id)


@router.put("/{category_id}", response_model=MaterialCategoryRead)
async def update_material_category(
    category_id: UUID,
    payload: MaterialCategoryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:standard:update"))],
) -> MaterialCategoryRead:
    return await svc.update_material_category(db, category_id, payload.model_dump(exclude_unset=True))


@router.delete("/{category_id}", response_model=MaterialCategoryRead)
async def delete_material_category(
    category_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:standard:delete"))],
) -> MaterialCategoryRead:
    return await svc.delete_material_category(db, category_id)
