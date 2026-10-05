from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.product import (
    ProductCostTemplateCreate,
    ProductCostTemplateRead,
    ProductCostTemplateUpdate,
)
from app.services import product_service as svc

router = APIRouter()


@router.post("", response_model=ProductCostTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_cost_template(
    payload: ProductCostTemplateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:product_cost_template:create"))],
) -> ProductCostTemplateRead:
    return await svc.create_cost_template(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse)
async def list_cost_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_cost_template:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
    product_id: UUID | None = None,
) -> PageResponse:
    return await svc.list_cost_templates(db, page, page_size, q, product_id)


@router.get("/{template_id}", response_model=ProductCostTemplateRead)
async def get_cost_template(
    template_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_cost_template:read"))],
) -> ProductCostTemplateRead:
    return await svc.get_cost_template_or_404(db, template_id)


@router.put("/{template_id}", response_model=ProductCostTemplateRead)
async def update_cost_template(
    template_id: UUID,
    payload: ProductCostTemplateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_cost_template:update"))],
) -> ProductCostTemplateRead:
    return await svc.update_cost_template(db, template_id, payload.model_dump(exclude_unset=True))


@router.delete("/{template_id}", response_model=ProductCostTemplateRead)
async def delete_cost_template(
    template_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product_cost_template:delete"))],
) -> ProductCostTemplateRead:
    return await svc.delete_cost_template(db, template_id)
