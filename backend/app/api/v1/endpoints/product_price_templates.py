from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.product import (
    ProductPriceTemplateCreate,
    ProductPriceTemplateRead,
    ProductPriceTemplateUpdate,
)
from app.services import product_service as svc

router = APIRouter()


@router.post("", response_model=ProductPriceTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_price_template(
    payload: ProductPriceTemplateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:product_price_template:create"))],
) -> ProductPriceTemplateRead:
    return await svc.create_price_template(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse[ProductPriceTemplateRead])
async def list_price_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_price_template:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
    product_id: UUID | None = None,
) -> PageResponse:
    return await svc.list_price_templates(db, page, page_size, q, product_id)


@router.get("/{template_id}", response_model=ProductPriceTemplateRead)
async def get_price_template(
    template_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_price_template:read"))],
) -> ProductPriceTemplateRead:
    return await svc.get_price_template_or_404(db, template_id)


@router.put("/{template_id}", response_model=ProductPriceTemplateRead)
async def update_price_template(
    template_id: UUID,
    payload: ProductPriceTemplateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_price_template:update"))],
) -> ProductPriceTemplateRead:
    return await svc.update_price_template(db, template_id, payload.model_dump(exclude_unset=True))


@router.delete("/{template_id}", response_model=ProductPriceTemplateRead)
async def delete_price_template(
    template_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_price_template:delete"))],
) -> ProductPriceTemplateRead:
    return await svc.delete_price_template(db, template_id)
