from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import (
    Product,
    ProductCategory,
    ProductCostTemplate,
    ProductCostTemplateLine,
    ProductPriceTemplate,
    ProductPriceTemplateLine,
)
from app.repositories.common_repository import get_by_id, paginate_query

# --- Categories ---


async def create_product_category(db: AsyncSession, data: dict) -> ProductCategory:
    obj = ProductCategory(**data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_product_categories(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
) -> tuple[int, list[ProductCategory]]:
    return await paginate_query(db, ProductCategory, page, page_size, q, [ProductCategory.code, ProductCategory.name])


async def get_product_category(db: AsyncSession, object_id: UUID) -> ProductCategory | None:
    return await get_by_id(db, ProductCategory, object_id)


async def update_product_category(db: AsyncSession, obj: ProductCategory, data: dict) -> ProductCategory:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_product_category(db: AsyncSession, obj: ProductCategory) -> ProductCategory:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj


# --- Products ---


async def create_product(db: AsyncSession, data: dict) -> Product:
    obj = Product(**data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_products(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    category_id: UUID | None = None,
) -> tuple[int, list[Product]]:
    extra = [Product.category_id == category_id] if category_id else []
    return await paginate_query(db, Product, page, page_size, q, [Product.code, Product.name, Product.spec], extra)


async def get_product(db: AsyncSession, object_id: UUID) -> Product | None:
    return await get_by_id(db, Product, object_id)


async def update_product(db: AsyncSession, obj: Product, data: dict) -> Product:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_product(db: AsyncSession, obj: Product) -> Product:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj


# --- Cost templates ---


async def create_cost_template(db: AsyncSession, data: dict, lines: list[dict]) -> ProductCostTemplate:
    line_rows = data.pop("lines", None)
    payload_lines = lines if lines is not None else (line_rows or [])
    obj = ProductCostTemplate(**data)
    for idx, line in enumerate(payload_lines):
        obj.lines.append(ProductCostTemplateLine(**line, sort_order=line.get("sort_order", idx)))
    db.add(obj)
    await db.commit()
    return await get_cost_template(db, obj.id)  # type: ignore[return-value]


async def list_cost_templates(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    product_id: UUID | None = None,
) -> tuple[int, list[ProductCostTemplate]]:
    extra = [ProductCostTemplate.product_id == product_id] if product_id else []
    return await paginate_query(
        db,
        ProductCostTemplate,
        page,
        page_size,
        q,
        [ProductCostTemplate.code, ProductCostTemplate.name],
        extra,
    )


async def get_cost_template(db: AsyncSession, object_id: UUID) -> ProductCostTemplate | None:
    stmt = (
        select(ProductCostTemplate)
        .where(ProductCostTemplate.id == object_id, ProductCostTemplate.is_deleted.is_(False))
        .options(selectinload(ProductCostTemplate.lines))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def update_cost_template(db: AsyncSession, obj: ProductCostTemplate, data: dict, lines: list[dict] | None) -> ProductCostTemplate:
    lines_payload = data.pop("lines", None)
    for key, value in data.items():
        setattr(obj, key, value)
    if lines is not None or lines_payload is not None:
        obj.lines.clear()
        for idx, line in enumerate(lines if lines is not None else lines_payload or []):
            obj.lines.append(ProductCostTemplateLine(**line, sort_order=line.get("sort_order", idx)))
    await db.commit()
    return await get_cost_template(db, obj.id)  # type: ignore[return-value]


async def soft_delete_cost_template(db: AsyncSession, obj: ProductCostTemplate) -> ProductCostTemplate:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj


async def find_default_cost_template(db: AsyncSession, product_id: UUID) -> ProductCostTemplate | None:
    product = await get_product(db, product_id)
    if product and product.default_cost_template_id:
        return await get_cost_template(db, product.default_cost_template_id)
    stmt = (
        select(ProductCostTemplate)
        .where(
            ProductCostTemplate.product_id == product_id,
            ProductCostTemplate.is_deleted.is_(False),
            ProductCostTemplate.status == "active",
        )
        .options(selectinload(ProductCostTemplate.lines))
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


# --- Price templates ---


async def create_price_template(db: AsyncSession, data: dict, lines: list[dict]) -> ProductPriceTemplate:
    line_rows = data.pop("lines", None)
    payload_lines = lines if lines is not None else (line_rows or [])
    obj = ProductPriceTemplate(**data)
    for idx, line in enumerate(payload_lines):
        obj.lines.append(ProductPriceTemplateLine(**line, sort_order=line.get("sort_order", idx)))
    db.add(obj)
    await db.commit()
    return await get_price_template(db, obj.id)  # type: ignore[return-value]


async def list_price_templates(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    product_id: UUID | None = None,
) -> tuple[int, list[ProductPriceTemplate]]:
    extra = [ProductPriceTemplate.product_id == product_id] if product_id else []
    return await paginate_query(
        db,
        ProductPriceTemplate,
        page,
        page_size,
        q,
        [ProductPriceTemplate.code, ProductPriceTemplate.name],
        extra,
    )


async def get_price_template(db: AsyncSession, object_id: UUID) -> ProductPriceTemplate | None:
    stmt = (
        select(ProductPriceTemplate)
        .where(ProductPriceTemplate.id == object_id, ProductPriceTemplate.is_deleted.is_(False))
        .options(selectinload(ProductPriceTemplate.lines))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def update_price_template(db: AsyncSession, obj: ProductPriceTemplate, data: dict, lines: list[dict] | None) -> ProductPriceTemplate:
    lines_payload = data.pop("lines", None)
    for key, value in data.items():
        setattr(obj, key, value)
    if lines is not None or lines_payload is not None:
        obj.lines.clear()
        for idx, line in enumerate(lines if lines is not None else lines_payload or []):
            obj.lines.append(ProductPriceTemplateLine(**line, sort_order=line.get("sort_order", idx)))
    await db.commit()
    return await get_price_template(db, obj.id)  # type: ignore[return-value]


async def soft_delete_price_template(db: AsyncSession, obj: ProductPriceTemplate) -> ProductPriceTemplate:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj


async def find_default_price_template(db: AsyncSession, product_id: UUID) -> ProductPriceTemplate | None:
    product = await get_product(db, product_id)
    if product and product.default_price_template_id:
        return await get_price_template(db, product.default_price_template_id)
    stmt = (
        select(ProductPriceTemplate)
        .where(
            ProductPriceTemplate.product_id == product_id,
            ProductPriceTemplate.is_deleted.is_(False),
            ProductPriceTemplate.status == "active",
        )
        .options(selectinload(ProductPriceTemplate.lines))
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()
