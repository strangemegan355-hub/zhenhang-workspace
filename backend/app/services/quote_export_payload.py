from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.domains.quote.public import queries as repo
from app.models.customer import Customer
from app.models.machine import Machine
from app.services import business_settings_service as business_settings_svc


async def build_export_payload(
    db: AsyncSession,
    quote_id: UUID,
    *,
    export_format: str,
    template_id: str | None = None,
) -> dict:
    quote = await repo.get_quote(db, quote_id)
    if quote is None:
        return {"format": export_format, "template_id": template_id, "items": []}

    customer_name = ""
    if quote.customer_id:
        customer = (await db.execute(select(Customer).where(Customer.id == quote.customer_id))).scalar_one_or_none()
        customer_name = customer.name if customer else ""

    machine_name = ""
    if quote.machine_id:
        machine = (await db.execute(select(Machine).where(Machine.id == quote.machine_id))).scalar_one_or_none()
        machine_name = machine.name if machine else ""

    version_no = await repo.max_quote_version_no(db, quote_id)
    version = await repo.get_quote_version_by_no(db, quote_id, version_no) if version_no > 0 else None
    items: list[dict] = []
    bom_snapshot = None
    if version:
        bom_snapshot = version.bom_snapshot
        for item in await repo.list_quote_items_by_version(db, version.id):
            items.append(
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "quantity": str(item.quantity),
                    "unit_price": str(item.unit_price),
                    "line_total": str(item.line_total),
                }
            )

    if not bom_snapshot and quote.bom_id:
        bom = await repo.get_bom(db, quote.bom_id)
        bom_items = await repo.list_bom_items(db, quote.bom_id)
        bom_snapshot = {
            "bom_id": str(quote.bom_id),
            "bom_version": bom.version if bom else None,
            "items": [
                {
                    "item_code": i.item_code,
                    "item_name": i.item_name,
                    "quantity": str(i.quantity),
                    "unit_cost": str(i.unit_cost),
                    "line_total": str(i.line_total),
                }
                for i in bom_items
            ],
        }

    total_amount = version.total_amount if version else quote.total_amount
    total_cost = version.total_cost if version else 0
    profit_amount = version.profit_amount if version else 0
    profit_rate = version.profit_rate if version else 0

    biz = await business_settings_svc.get_business_settings_dict(db)
    company_name = biz.get("company_name") or settings.company_name
    footer_note = biz.get("export_footer") or settings.company_export_footer

    return {
        "format": export_format,
        "template_id": template_id,
        "quote_no": quote.quote_no,
        "title": quote.title,
        "customer_name": customer_name,
        "machine_name": machine_name,
        "currency": quote.currency,
        "workflow_state": quote.workflow_state,
        "version_no": version_no or 1,
        "printed_at": date.today().isoformat(),
        "remark": quote.remark,
        "items": items,
        "bom_snapshot": bom_snapshot,
        "total_amount": str(total_amount),
        "total_cost": str(total_cost),
        "profit_amount": str(profit_amount),
        "profit_rate": str(profit_rate),
        "company_name": company_name,
        "footer_note": footer_note,
        "default_tax_rate": biz.get("default_tax_rate"),
        "default_currency": biz.get("default_currency") or quote.currency,
    }
