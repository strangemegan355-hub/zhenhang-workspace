"""Quote item options, moved out of the flat service layer in round 44.

It was `app/services/quote_option_service.py`; inside the domain it reads quotes through the
domain's repository and reaches option-group data through the legacy service rather than its
repository, which gate 4 forbids from a domain file.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import scope_predicate
from app.domains.quote.repositories import quote_repository as repo
from app.models.quote import Quote
from app.services import option_group_service as opt_svc


async def update_quote_item_options(
    db: AsyncSession, quote_id: UUID, item_id: UUID, option_item_ids: list[UUID], current_user
) -> dict:
    quote = await repo.get_quote(db, quote_id, predicate=scope_predicate(Quote, current_user))
    if quote is None:
        raise ValueError(f"报价 {quote_id} 不存在")

    current_version = await repo.get_current_quote_version(db, quote.id)
    if current_version is None:
        raise ValueError(f"报价 {quote_id} 无当前版本")

    item = await repo.get_quote_item(db, item_id)
    if item is None or item.quote_version_id != current_version.id:
        raise ValueError(f"报价行 {item_id} 不存在")

    price_adjustment = Decimal("0")
    if option_item_ids:
        options = await opt_svc.get_option_items_by_ids(db, option_item_ids)
        found_ids = {o.id for o in options}
        for oid in option_item_ids:
            if oid not in found_ids:
                raise ValueError(f"选项 {oid} 不存在")
        price_adjustment = sum((Decimal(str(o.price_adjustment)) for o in options), Decimal("0"))

    item.selected_options = [str(oid) for oid in option_item_ids]
    base_price = Decimal(str(item.unit_price))
    new_unit_price = base_price + price_adjustment
    item.unit_price = new_unit_price
    item.line_total = new_unit_price * Decimal(str(item.quantity))

    await db.flush()

    # Recalculate version totals
    items = await repo.list_quote_items_by_version(db, current_version.id)
    total = sum((i.line_total for i in items), Decimal("0"))
    current_version.total_amount = total
    current_version.total_cost = current_version.total_cost or Decimal("0")
    current_version.profit_amount = total - current_version.total_cost
    current_version.profit_rate = Decimal("0") if total == 0 else (current_version.profit_amount / total)

    quote.total_amount = total
    await db.commit()

    return {
        "id": item.id,
        "quote_version_id": item.quote_version_id,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "spec": item.spec,
        "unit": item.unit,
        "quantity": item.quantity,
        "unit_price": item.unit_price,
        "line_total": item.line_total,
        "source_type": item.source_type,
        "machine_id": item.machine_id,
        "product_id": item.product_id,
        "power_kw": item.power_kw,
        "remark": item.remark,
        "selected_options": item.selected_options,
    }
