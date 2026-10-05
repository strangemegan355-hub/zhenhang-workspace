from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import product_repository as repo
from app.schemas.product import ProductQuotePayload


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


async def build_product_quote_payload(
    db: AsyncSession,
    product_id: UUID,
    *,
    cost_template_id: UUID | None = None,
    price_template_id: UUID | None = None,
) -> ProductQuotePayload:
    product = await repo.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    cost_tpl = None
    if cost_template_id:
        cost_tpl = await repo.get_cost_template(db, cost_template_id)
    if cost_tpl is None:
        cost_tpl = await repo.find_default_cost_template(db, product_id)

    price_tpl = None
    if price_template_id:
        price_tpl = await repo.get_price_template(db, price_template_id)
    if price_tpl is None:
        price_tpl = await repo.find_default_price_template(db, product_id)

    if price_tpl and price_tpl.cost_template_id and cost_tpl is None:
        cost_tpl = await repo.get_cost_template(db, price_tpl.cost_template_id)

    margin = Decimal(str(price_tpl.margin_rate if price_tpl else Decimal("0.25")))
    lines: list[dict] = []

    if price_tpl and price_tpl.lines:
        for line in price_tpl.lines:
            unit_cost = Decimal(str(line.unit_cost))
            unit_price = Decimal(str(line.unit_price))
            if unit_price <= 0 and unit_cost > 0:
                unit_price = _quantize(unit_cost * (Decimal("1") + margin))
            lines.append(
                {
                    "item_code": line.item_code,
                    "item_name": line.item_name,
                    "unit": line.unit,
                    "quantity": Decimal(str(line.quantity)),
                    "unit_cost": unit_cost,
                    "unit_price": unit_price,
                    "source_type": "product",
                }
            )
    elif cost_tpl and cost_tpl.lines:
        overhead = Decimal(str(cost_tpl.overhead_rate or 0))
        scrap = Decimal(str(cost_tpl.scrap_rate or 0))
        for line in cost_tpl.lines:
            unit_cost = Decimal(str(line.unit_cost))
            adjusted_cost = _quantize(unit_cost * (Decimal("1") + scrap + overhead))
            unit_price = _quantize(adjusted_cost * (Decimal("1") + margin))
            lines.append(
                {
                    "item_code": line.item_code,
                    "item_name": line.item_name,
                    "unit": line.unit,
                    "quantity": Decimal(str(line.quantity)),
                    "unit_cost": adjusted_cost,
                    "unit_price": unit_price,
                    "source_type": "product",
                }
            )
    else:
        ref_cost = Decimal(str(product.reference_cost or 0))
        ref_price = Decimal(str(product.reference_price or 0))
        if ref_price <= 0 and ref_cost > 0:
            ref_price = _quantize(ref_cost * (Decimal("1") + margin))
        lines.append(
            {
                "item_code": product.code,
                "item_name": product.name,
                "unit": product.unit,
                "quantity": Decimal("1"),
                "unit_cost": ref_cost,
                "unit_price": ref_price if ref_price > 0 else _quantize(ref_cost * (Decimal("1") + margin)),
                "source_type": "product",
            }
        )

    return ProductQuotePayload(
        product_id=product.id,
        product_code=product.code,
        product_name=product.name,
        spec=product.spec,
        cost_template_id=cost_tpl.id if cost_tpl else None,
        price_template_id=price_tpl.id if price_tpl else None,
        margin_rate=margin,
        machine_id=product.machine_id,
        default_bom_id=product.default_bom_id,
        lines=lines,
    )


async def build_product_quote_items(
    db: AsyncSession,
    product_id: UUID,
    *,
    cost_template_id: UUID | None = None,
    price_template_id: UUID | None = None,
) -> list[dict]:
    payload = await build_product_quote_payload(
        db,
        product_id,
        cost_template_id=cost_template_id,
        price_template_id=price_template_id,
    )
    return [
        {
            "item_code": line.item_code,
            "item_name": line.item_name,
            "spec": payload.spec,
            "unit": line.unit,
            "quantity": line.quantity,
            "unit_price": line.unit_price,
            "source_type": "product",
            "remark": f"product:{payload.product_code}",
        }
        for line in payload.lines
    ]
