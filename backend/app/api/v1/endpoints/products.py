from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.product import ProductCreate, ProductQuotePayload, ProductRead, ProductUpdate
from app.services import product_service as svc
from app.services.product_pricing_service import build_product_quote_payload

router = APIRouter()


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:product:create"))],
) -> ProductRead:
    return await svc.create_product(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse[ProductRead])
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
    category_id: UUID | None = None,
) -> PageResponse:
    return await svc.list_products(db, page, page_size, q, category_id)


@router.get("/{product_id}/quote-payload", response_model=ProductQuotePayload)
async def get_product_quote_payload(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:quote:read"))],
    cost_template_id: UUID | None = None,
    price_template_id: UUID | None = None,
) -> ProductQuotePayload:
    return await build_product_quote_payload(
        db,
        product_id,
        cost_template_id=cost_template_id,
        price_template_id=price_template_id,
    )


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product:read"))],
) -> ProductRead:
    return await svc.get_product_or_404(db, product_id)


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product:update"))],
) -> ProductRead:
    return await svc.update_product(db, product_id, payload.model_dump(exclude_unset=True))


@router.delete("/{product_id}", response_model=ProductRead)
async def delete_product(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:product:delete"))],
) -> ProductRead:
    return await svc.delete_product(db, product_id)
