from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.product import ProductCategoryCreate, ProductCategoryRead, ProductCategoryUpdate
from app.services import product_service as svc

router = APIRouter()


@router.post("", response_model=ProductCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_product_category(
    payload: ProductCategoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:product_category:create"))],
) -> ProductCategoryRead:
    return await svc.create_product_category(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse[ProductCategoryRead])
async def list_product_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_category:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_product_categories(db, page, page_size, q)


@router.get("/{category_id}", response_model=ProductCategoryRead)
async def get_product_category(
    category_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_category:read"))],
) -> ProductCategoryRead:
    return await svc.get_product_category_or_404(db, category_id)


@router.put("/{category_id}", response_model=ProductCategoryRead)
async def update_product_category(
    category_id: UUID,
    payload: ProductCategoryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_category:update"))],
) -> ProductCategoryRead:
    return await svc.update_product_category(db, category_id, payload.model_dump(exclude_unset=True))


@router.delete("/{category_id}", response_model=ProductCategoryRead)
async def delete_product_category(
    category_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_category:delete"))],
) -> ProductCategoryRead:
    return await svc.delete_product_category(db, category_id)
