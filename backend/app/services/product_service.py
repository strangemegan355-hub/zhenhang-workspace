from decimal import Decimal
from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import product_repository as repo
from app.schemas.common import PageResponse
from app.schemas.product import (
    ProductCategoryRead,
    ProductCostTemplateRead,
    ProductPriceTemplateRead,
    ProductQuotePayload,
    ProductRead,
)
from app.schemas.common import page_response as _page

T = TypeVar("T", bound=BaseModel)

# --- Categories ---

async def create_product_category(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    obj = await repo.create_product_category(db, payload)
    return ProductCategoryRead.model_validate(obj)

async def list_product_categories(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, items = await repo.list_product_categories(db, page, page_size, q)
    return _page(total, page, page_size, items, ProductCategoryRead)

async def get_product_category_or_404(db: AsyncSession, object_id: UUID):
    obj = await repo.get_product_category(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product category not found")
    return ProductCategoryRead.model_validate(obj)

async def update_product_category(db: AsyncSession, object_id: UUID, payload: dict):
    obj = await repo.get_product_category(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product category not found")
    updated = await repo.update_product_category(db, obj, payload)
    return ProductCategoryRead.model_validate(updated)

async def delete_product_category(db: AsyncSession, object_id: UUID):
    obj = await repo.get_product_category(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product category not found")
    deleted = await repo.soft_delete_product_category(db, obj)
    return ProductCategoryRead.model_validate(deleted)

# --- Products ---

async def create_product(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    obj = await repo.create_product(db, payload)
    return ProductRead.model_validate(obj)

async def list_products(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    category_id: UUID | None = None,
) -> PageResponse:
    total, items = await repo.list_products(db, page, page_size, q, category_id)
    return _page(total, page, page_size, items, ProductRead)

async def get_product_or_404(db: AsyncSession, object_id: UUID):
    obj = await repo.get_product(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductRead.model_validate(obj)

async def get_product_or_none(db: AsyncSession, object_id: UUID):
    """The product model, or None when it does not exist.

    `get_product_or_404` cannot serve callers that tolerate absence — the quote creation path seeds
    machine and BOM defaults only if a product was found — and it returns a validated `ProductRead`
    where such callers read ORM attributes. This keeps them on the service layer, which is the legacy
    layer's public surface, instead of reaching into its repository.
    """
    return await repo.get_product(db, object_id)

async def update_product(db: AsyncSession, object_id: UUID, payload: dict):
    obj = await repo.get_product(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    updated = await repo.update_product(db, obj, payload)
    return ProductRead.model_validate(updated)

async def delete_product(db: AsyncSession, object_id: UUID):
    obj = await repo.get_product(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    deleted = await repo.soft_delete_product(db, obj)
    return ProductRead.model_validate(deleted)

# --- Cost templates ---

async def create_cost_template(db: AsyncSession, payload: dict, current_user: User):
    lines = payload.pop("lines", [])
    payload["created_by"] = current_user.id
    obj = await repo.create_cost_template(db, payload, lines)
    return ProductCostTemplateRead.model_validate(obj)

async def list_cost_templates(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    product_id: UUID | None = None,
) -> PageResponse:
    total, items = await repo.list_cost_templates(db, page, page_size, q, product_id)
    hydrated = []
    for item in items:
        full = await repo.get_cost_template(db, item.id)
        hydrated.append(full or item)
    return _page(total, page, page_size, hydrated, ProductCostTemplateRead)

async def get_cost_template_or_404(db: AsyncSession, object_id: UUID):
    obj = await repo.get_cost_template(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost template not found")
    return ProductCostTemplateRead.model_validate(obj)

async def update_cost_template(db: AsyncSession, object_id: UUID, payload: dict):
    obj = await repo.get_cost_template(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost template not found")
    lines = payload.pop("lines", None)
    updated = await repo.update_cost_template(db, obj, payload, lines)
    return ProductCostTemplateRead.model_validate(updated)

async def delete_cost_template(db: AsyncSession, object_id: UUID):
    obj = await repo.get_cost_template(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost template not found")
    deleted = await repo.soft_delete_cost_template(db, obj)
    return ProductCostTemplateRead.model_validate(deleted)

# --- Price templates ---

async def create_price_template(db: AsyncSession, payload: dict, current_user: User):
    lines = payload.pop("lines", [])
    payload["created_by"] = current_user.id
    obj = await repo.create_price_template(db, payload, lines)
    return ProductPriceTemplateRead.model_validate(obj)

async def list_price_templates(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    product_id: UUID | None = None,
) -> PageResponse:
    total, items = await repo.list_price_templates(db, page, page_size, q, product_id)
    hydrated = []
    for item in items:
        full = await repo.get_price_template(db, item.id)
        hydrated.append(full or item)
    return _page(total, page, page_size, hydrated, ProductPriceTemplateRead)

async def get_price_template_or_404(db: AsyncSession, object_id: UUID):
    obj = await repo.get_price_template(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price template not found")
    return ProductPriceTemplateRead.model_validate(obj)

async def update_price_template(db: AsyncSession, object_id: UUID, payload: dict):
    obj = await repo.get_price_template(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price template not found")
    lines = payload.pop("lines", None)
    updated = await repo.update_price_template(db, obj, payload, lines)
    return ProductPriceTemplateRead.model_validate(updated)

async def delete_price_template(db: AsyncSession, object_id: UUID):
    obj = await repo.get_price_template(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price template not found")
    deleted = await repo.soft_delete_price_template(db, obj)
    return ProductPriceTemplateRead.model_validate(deleted)
