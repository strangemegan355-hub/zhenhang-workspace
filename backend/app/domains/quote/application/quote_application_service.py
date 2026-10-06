from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.domains.events.application.event_bus import event_bus
from app.core.data_scope import scope_predicate
from app.domains.quote.repositories import quote_repository as repo
from app.models.quote import Quote
from app.notifications.notification_service import create_notification
from app.schemas.common import PageResponse
from app.schemas.quote import ApprovalTemplateRead, QuoteItemRead, QuoteRead, QuoteVersionRead
from app.realtime.publish import push_quote_export_status, push_quote_updated, push_workflow_transition
from app.services.business_settings_service import get_business_settings_dict
from app.services.audit_service import write_audit_log
from app.services.industrial_copilot import build_industrial_copilot_analysis
from app.services.quote_template_engine import list_template_catalog
from app.services.workflow_service import get_next_state_code


def _quote_prefix() -> str:
    return f"Q{date.today().strftime('%Y%m%d')}-"


async def create_quote(db: AsyncSession, payload: dict, current_user):
    seq = await repo.next_quote_sequence(db, _quote_prefix())
    quote_no = f"{_quote_prefix()}{seq:04d}"
    obj = await repo.create_quote(
        db,
        {
            **payload,
            "quote_no": quote_no,
            "total_amount": Decimal("0"),
            "current_approval_order": 0,
            "created_by": current_user.id,
        },
        autocommit=False,
    )
    await write_audit_log(
        db,
        module="quote",
        action="create",
        resource_type="quote",
        resource_id=obj.id,
        created_by=current_user.id,
        payload={"quote_no": quote_no},
        autocommit=False,
    )
    await event_bus.publish(
        db,
        event_type="quote.created",
        aggregate_type="quote",
        aggregate_id=obj.id,
        payload={"quote_id": obj.id, "quote_no": quote_no, "created_by": current_user.id},
        created_by=current_user.id,
    )
    await create_notification(
        db,
        title="报价已创建",
        content=f"报价 {quote_no} 已创建",
        biz_type="quote",
        biz_id=obj.id,
        receiver_id=current_user.id,
        payload={"quote_no": quote_no},
        created_by=current_user.id,
        autocommit=False,
    )
    await db.commit()
    await db.refresh(obj)
    await push_quote_updated(
        quote_id=obj.id,
        quote_no=quote_no,
        event="quote.created",
        owner_id=current_user.id,
        department_id=getattr(current_user, "department_id", None),
    )
    return obj


async def create_quote_version(db: AsyncSession, quote_id: UUID, items_payload: list[dict], current_user):
    quote = await repo.get_quote(db, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")

    next_version = await repo.max_quote_version_no(db, quote.id) + 1
    bom_snapshot = None
    cost_snapshot = None
    if quote.bom_id:
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
        cost_snapshot = {
            "bom_total_cost": str(bom.total_cost) if bom else "0",
            "captured_at": datetime.now(UTC).isoformat(),
        }
    previous_version = await repo.get_quote_version_by_no(db, quote.id, next_version - 1) if next_version > 1 else None
    await repo.mark_other_versions_not_current(db, quote.id)
    version = await repo.create_quote_version(
        db,
        {
            "quote_id": quote.id,
            "version_no": next_version,
            "bom_snapshot": bom_snapshot,
            "cost_snapshot": cost_snapshot,
            "analysis_snapshot": {},
            "total_amount": Decimal("0"),
            "total_cost": Decimal("0"),
            "profit_amount": Decimal("0"),
            "profit_rate": Decimal("0"),
            "is_current": True,
            "changed_at": datetime.now(UTC),
            "created_by": current_user.id,
        },
        autocommit=False,
    )
    total_amount = Decimal("0")
    for item in items_payload:
        qty = Decimal(str(item["quantity"]))
        price = Decimal(str(item["unit_price"]))
        line_total = qty * price
        total_amount += line_total
        await repo.create_quote_item(
            db,
            {
                "quote_version_id": version.id,
                "item_code": item["item_code"],
                "item_name": item["item_name"],
                "spec": item.get("spec"),
                "unit": item["unit"],
                "quantity": qty,
                "unit_price": price,
                "line_total": line_total,
                "source_type": item.get("source_type", "manual"),
                "machine_id": item.get("machine_id"),
                "power_kw": item.get("power_kw"),
                "remark": item.get("remark"),
                "created_by": current_user.id,
            },
            autocommit=False,
        )
    version.total_amount = total_amount
    total_cost = Decimal(str((cost_snapshot or {}).get("bom_total_cost", "0")))
    version.total_cost = total_cost
    version.profit_amount = total_amount - total_cost
    version.profit_rate = Decimal("0") if total_amount == 0 else (version.profit_amount / total_amount)
    if previous_version:
        diff_data = await compare_quote_versions(db, quote.id, previous_version.version_no, next_version)
        version.analysis_snapshot = diff_data
    quote.total_amount = total_amount
    await write_audit_log(
        db,
        module="quote",
        action="create_version",
        resource_type="quote_version",
        resource_id=version.id,
        created_by=current_user.id,
        payload={"quote_id": str(quote.id), "version_no": next_version},
        autocommit=False,
    )
    await create_notification(
        db,
        title="报价版本已更新",
        content=f"报价 {quote.quote_no} 已生成版本 V{next_version}",
        biz_type="quote",
        biz_id=quote.id,
        receiver_id=current_user.id,
        payload={"version_no": next_version},
        created_by=current_user.id,
        autocommit=False,
    )
    await event_bus.publish(
        db,
        event_type="quote.version.created",
        aggregate_type="quote",
        aggregate_id=quote.id,
        payload={"quote_id": quote.id, "version_id": version.id, "version_no": next_version, "created_by": current_user.id},
        created_by=current_user.id,
    )
    await db.commit()
    await db.refresh(version)
    await push_quote_updated(
        quote_id=quote.id,
        quote_no=quote.quote_no,
        event="quote.version_created",
        owner_id=quote.created_by,
        department_id=getattr(current_user, "department_id", None),
    )
    return version


async def list_quotes(db: AsyncSession, *, page: int, page_size: int, q: str | None, current_user, quote_kind: str | None = None):
    # The scope is pushed into SQL, so a department-scoped role sees its department's quotes
    # instead of only the rows it created itself.
    total, items = await repo.list_quotes(
        db,
        page=page,
        page_size=page_size,
        q=q,
        predicate=scope_predicate(Quote, current_user),
        quote_kind=quote_kind,
    )
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[QuoteRead.model_validate(i) for i in items],
    )


async def get_quote_detail(db: AsyncSession, quote_id: UUID, current_user):
    quote = await repo.get_quote(db, quote_id, predicate=scope_predicate(Quote, current_user))
    if quote is None:
        # An out-of-scope quote is reported exactly like an absent one: a 403 would confirm to
        # somebody who may not read it that the quote exists.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    current_version = await repo.get_current_quote_version(db, quote.id)
    items = []
    if current_version:
        items = await repo.list_quote_items_by_version(db, current_version.id)
    return {
        **QuoteRead.model_validate(quote).model_dump(),
        "current_version": QuoteVersionRead.model_validate(current_version) if current_version else None,
        "items": [QuoteItemRead.model_validate(i) for i in items],
    }


async def list_quote_versions(db: AsyncSession, quote_id: UUID, current_user):
    quote = await repo.get_quote(db, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    versions = await repo.list_quote_versions(db, quote_id)
    return versions


async def list_quote_approvals(db: AsyncSession, quote_id: UUID):
    quote = await repo.get_quote(db, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    return await repo.list_quote_approvals(db, quote_id)


async def get_approval_template_detail(db: AsyncSession, template_id: UUID):
    template = await repo.get_approval_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval template not found")
    nodes = await repo.list_approval_nodes(db, template_id)
    return {"template": template, "nodes": nodes}


async def list_export_templates() -> list[dict]:
    return list_template_catalog()


async def create_quote_wizard(db: AsyncSession, payload: dict, current_user):
    initial_items = payload.pop("initial_items", [])
    seed_from_product = payload.pop("seed_from_product", True)
    quote_payload = {k: v for k, v in payload.items() if k != "initial_items"}
    product_id = quote_payload.get("product_id")
    if product_id and not quote_payload.get("machine_id"):
        from app.services.product_service import get_product_or_none

        product = await get_product_or_none(db, product_id)
        if product:
            if product.machine_id and not quote_payload.get("machine_id"):
                quote_payload["machine_id"] = product.machine_id
            if product.default_bom_id and not quote_payload.get("bom_id"):
                quote_payload["bom_id"] = product.default_bom_id

    quote = await create_quote(db, quote_payload, current_user)

    items_payload = list(initial_items)
    bom_id = quote.bom_id
    if not items_payload and product_id and seed_from_product:
        from app.services.product_pricing_service import build_product_quote_items

        items_payload = await build_product_quote_items(
            db,
            product_id,
            cost_template_id=quote.cost_template_id,
            price_template_id=quote.price_template_id,
        )
    if not items_payload and bom_id:
        bom_items = await repo.list_bom_items(db, bom_id)
        for bi in bom_items:
            cost = Decimal(str(bi.unit_cost))
            items_payload.append(
                {
                    "item_code": bi.item_code,
                    "item_name": bi.item_name,
                    "spec": bi.spec,
                    "unit": bi.unit,
                    "quantity": Decimal(str(bi.quantity)),
                    "unit_price": (cost * Decimal("1.25")).quantize(Decimal("0.01")),
                    "source_type": "bom",
                    "remark": bi.remark,
                }
            )

    if items_payload:
        await create_quote_version(db, quote.id, items_payload, current_user)
        quote = await repo.get_quote(db, quote.id)

    return await get_quote_detail(db, quote.id, current_user)


async def summarize_quote_for_copilot(
    db: AsyncSession,
    quote_id: UUID,
    *,
    from_version_no: int | None = None,
    to_version_no: int | None = None,
) -> dict:
    quote = await repo.get_quote(db, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    return await build_industrial_copilot_analysis(
        db,
        quote_id,
        from_version_no=from_version_no,
        to_version_no=to_version_no,
        compare_fn=compare_quote_versions,
    )


async def transition_quote_state(db: AsyncSession, quote_id: UUID, action_code: str, comment: str | None, current_user):
    quote = await repo.get_quote(db, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    old_state = quote.workflow_state
    next_state = await get_next_state_code(
        db,
        entity_type="quote",
        current_state_code=quote.workflow_state,
        action_code=action_code,
    )
    current_node = await current_approval_node(db, quote)
    if current_node is not None and action_code in {"approve", "reject"}:
        await repo.create_approval_record(
            db,
            {
                "quote_id": quote.id,
                "template_id": quote.approval_template_id,
                "node_id": current_node.id,
                "approver_id": current_user.id,
                "action": action_code,
                "status": next_state,
                "comment": comment,
                "acted_at": datetime.now(UTC),
                "created_by": current_user.id,
            },
            autocommit=False,
        )
        if current_node.sign_mode == "countersign" and action_code == "approve":
            approved_count = await repo.count_approval_records(
                db,
                quote_id=quote.id,
                node_id=current_node.id,
                action="approve",
            )
            # Minimal countersign policy: require at least 2 approvals for countersign nodes.
            if approved_count < 2:
                next_state = "reviewing"
    next_node = await resolve_next_approval_node(db, quote)
    if next_node and action_code in {"submit", "approve"}:
        quote.current_approval_order = max(quote.current_approval_order, next_node.node_order)
    await repo.update_quote_state(db, quote, next_state)
    await repo.create_quote_approval(
        db,
        {
            "quote_id": quote.id,
            "approver_id": current_user.id,
            "action": action_code,
            "status": next_state,
            "comment": comment,
            "acted_at": datetime.now(UTC),
            "created_by": current_user.id,
        },
        autocommit=False,
    )
    await write_audit_log(
        db,
        module="quote",
        action="transition",
        resource_type="quote",
        resource_id=quote.id,
        created_by=current_user.id,
        detail=f"{old_state}->{next_state}",
        payload={"action_code": action_code},
        autocommit=False,
    )
    await create_notification(
        db,
        title="报价状态变更",
        content=f"报价 {quote.quote_no} 状态: {old_state} -> {next_state}",
        biz_type="quote",
        biz_id=quote.id,
        receiver_id=current_user.id,
        payload={"from": old_state, "to": next_state},
        created_by=current_user.id,
        autocommit=False,
    )
    await event_bus.publish(
        db,
        event_type="quote.transitioned",
        aggregate_type="quote",
        aggregate_id=quote.id,
        payload={"quote_id": quote.id, "state": next_state, "created_by": current_user.id},
        created_by=current_user.id,
    )
    await db.commit()
    await db.refresh(quote)
    await push_workflow_transition(
        quote_id=quote.id,
        quote_no=quote.quote_no,
        from_state=old_state,
        to_state=next_state,
        action_code=action_code,
        actor_id=current_user.id,
        owner_id=quote.created_by,
        department_id=getattr(current_user, "department_id", None),
    )
    return QuoteRead.model_validate(quote)


async def create_approval_template(db: AsyncSession, payload: dict, current_user):
    template_data = payload["template"]
    nodes = payload.get("nodes", [])
    template = await repo.create_approval_template(
        db,
        {
            "code": template_data["code"],
            "name": template_data["name"],
            "biz_type": "quote",
            "description": template_data.get("description"),
            "is_active": template_data.get("is_active", True),
            "created_by": current_user.id,
        },
        autocommit=False,
    )
    for node in nodes:
        await repo.create_approval_node(
            db,
            {
                "template_id": template.id,
                "node_order": node["node_order"],
                "node_name": node["node_name"],
                "approver_role_code": node.get("approver_role_code"),
                "sign_mode": node.get("sign_mode", "orsign"),
                "dynamic_approver_expr": node.get("dynamic_approver_expr"),
                "min_amount": node.get("min_amount", 0),
                "max_amount": node.get("max_amount"),
                "created_by": current_user.id,
            },
            autocommit=False,
        )
    await db.commit()
    await db.refresh(template)
    return template


async def list_approval_templates(db: AsyncSession, *, page: int, page_size: int, q: str | None):
    total, items = await repo.list_approval_templates(db, page=page, page_size=page_size, q=q)
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ApprovalTemplateRead.model_validate(i) for i in items],
    )


async def compare_quote_versions(db: AsyncSession, quote_id: UUID, from_version_no: int, to_version_no: int) -> dict:
    v_from = await repo.get_quote_version_by_no(db, quote_id, from_version_no)
    v_to = await repo.get_quote_version_by_no(db, quote_id, to_version_no)
    if v_from is None or v_to is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote version not found")
    items_from = await repo.list_quote_items_by_version(db, v_from.id)
    items_to = await repo.list_quote_items_by_version(db, v_to.id)
    map_from = {i.item_code: i for i in items_from}
    map_to = {i.item_code: i for i in items_to}
    added = sorted(set(map_to) - set(map_from))
    removed = sorted(set(map_from) - set(map_to))
    changed = []
    for code in sorted(set(map_from) & set(map_to)):
        a = map_from[code]
        b = map_to[code]
        if (a.quantity, a.unit_price, a.line_total) != (b.quantity, b.unit_price, b.line_total):
            changed.append(
                {
                    "item_code": code,
                    "from": {"quantity": str(a.quantity), "unit_price": str(a.unit_price), "line_total": str(a.line_total)},
                    "to": {"quantity": str(b.quantity), "unit_price": str(b.unit_price), "line_total": str(b.line_total)},
                }
            )
    cost_change = Decimal(str(v_to.total_cost)) - Decimal(str(v_from.total_cost))
    amount_change = Decimal(str(v_to.total_amount)) - Decimal(str(v_from.total_amount))
    profit_change = Decimal(str(v_to.profit_amount)) - Decimal(str(v_from.profit_amount))
    return {
        "from_version": from_version_no,
        "to_version": to_version_no,
        "bom_diff": {"added": added, "removed": removed, "changed": changed},
        "cost_change": str(cost_change),
        "amount_change": str(amount_change),
        "profit_change": str(profit_change),
        "profit_rate_change": str(Decimal(str(v_to.profit_rate)) - Decimal(str(v_from.profit_rate))),
    }


async def create_export_task(
    db: AsyncSession,
    quote_id: UUID,
    export_format: str,
    current_user,
    *,
    template_id: str | None = None,
):
    quote = await repo.get_quote(db, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    task = await repo.create_export_task(
        db,
        {
            "quote_id": quote.id,
            "format": export_format,
            "status": "pending",
            "requested_at": datetime.now(UTC),
            "created_by": current_user.id,
        },
        autocommit=False,
    )
    await event_bus.publish(
        db,
        event_type="quote.export.requested",
        aggregate_type="quote_export_task",
        aggregate_id=task.id,
        payload={
            "task_id": task.id,
            "quote_id": quote.id,
            "format": export_format,
            "template_id": template_id,
            "created_by": current_user.id,
        },
        created_by=current_user.id,
        dispatch_immediately=settings.app_env == "local",
    )
    await create_notification(
        db,
        title="报价导出任务已创建",
        content=f"报价 {quote.quote_no} 导出任务已创建 ({export_format})",
        biz_type="quote_export",
        biz_id=task.id,
        receiver_id=current_user.id,
        payload={"format": export_format, "template_id": template_id},
        created_by=current_user.id,
        autocommit=False,
    )
    await db.commit()
    await db.refresh(task)
    if task.status == "pending":
        await event_bus.process_pending(db, event_type="quote.export.requested", limit=20)
        await db.refresh(task)
    await push_quote_export_status(
        user_id=current_user.id,
        task_id=task.id,
        quote_id=quote.id,
        quote_no=quote.quote_no,
        status=task.status,
        file_id=task.file_id,
        owner_id=quote.created_by,
    )
    return task


async def get_export_task(db: AsyncSession, task_id: UUID):
    task = await repo.get_export_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export task not found")
    return task


async def replay_dead_letter_events(db: AsyncSession, event_type: str | None):
    return await event_bus.replay_dead_letters(db, event_type=event_type, limit=200)


async def process_pending_events(db: AsyncSession, event_type: str | None):
    result = await event_bus.process_pending(db, event_type=event_type, limit=200)
    await db.commit()
    return result


async def resolve_next_approval_node(db: AsyncSession, quote) -> object | None:
    if not quote.approval_template_id:
        return None
    nodes = await repo.list_approval_nodes(db, quote.approval_template_id)
    if not nodes:
        return None
    amount = Decimal(str(quote.total_amount or 0))
    for node in nodes:
        min_amount = Decimal(str(node.min_amount))
        max_amount = Decimal(str(node.max_amount)) if node.max_amount is not None else None
        if amount < min_amount:
            continue
        if max_amount is not None and amount > max_amount:
            continue
        if node.node_order > quote.current_approval_order:
            return node
    return None


def _quote_prefix() -> str:
    return f"Q{date.today().strftime('%Y%m%d')}-"


def _customer_quote_prefix() -> str:
    return f"BJ-{date.today().strftime('%Y%m%d')}-"


def _machine_lines_to_items(machine_lines: list[dict]) -> list[dict]:
    items: list[dict] = []
    for idx, line in enumerate(machine_lines):
        items.append(
            {
                "item_code": f"MACH-{idx + 1:03d}",
                "item_name": line["name"],
                "spec": line.get("spec"),
                "unit": line.get("unit") or "台",
                "quantity": Decimal(str(line.get("quantity", 1))),
                "unit_price": Decimal(str(line.get("unit_price", 0))),
                "source_type": "product" if line.get("product_id") else "machine",
                "machine_id": line.get("machine_id"),
                "product_id": line.get("product_id"),
                "power_kw": line.get("power_kw"),
            }
        )
        motor_product_id = line.get("motor_product_id")
        motor_unit_price = Decimal(str(line.get("motor_unit_price") or 0))
        if motor_product_id and motor_unit_price > 0:
            items.append(
                {
                    "item_code": f"MOTOR-{idx + 1:03d}",
                    "item_name": f"配套电机-{line.get('power_kw') or line.get('name') or '电机'}",
                    "spec": line.get("power_kw"),
                    "unit": "台",
                    "quantity": Decimal(str(line.get("quantity", 1))),
                    "unit_price": motor_unit_price,
                    "source_type": "product",
                    "machine_id": None,
                    "product_id": motor_product_id,
                    "power_kw": line.get("power_kw"),
                }
            )
    return items


async def _resolve_tax_rate(db: AsyncSession, tax_rate: float | None) -> Decimal:
    if tax_rate is not None:
        return Decimal(str(tax_rate))
    defaults = await get_business_settings_dict(db)
    return Decimal(str(defaults.get("default_tax_rate", 13)))


async def _apply_customer_quote_totals(db: AsyncSession, quote, version, *, tax_rate: Decimal, subtotal: Decimal) -> None:
    tax_amount = (subtotal * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
    final_total = (subtotal + tax_amount).quantize(Decimal("0.01"))
    version.total_amount = subtotal
    version.total_cost = Decimal("0")
    version.profit_amount = final_total - subtotal
    version.profit_rate = Decimal("0") if final_total == 0 else (version.profit_amount / final_total)
    version.analysis_snapshot = {
        "quote_kind": "customer",
        "tax_rate": str(tax_rate),
        "before_tax": str(subtotal),
        "tax_amount": str(tax_amount),
        "final_total": str(final_total),
    }
    quote.total_amount = final_total
    quote.tax_rate = tax_rate
    await db.flush()


async def create_customer_quote(db: AsyncSession, payload: dict, current_user):
    machine_lines = payload.get("machine_lines") or []
    if not machine_lines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one machine line is required")

    tax_rate = await _resolve_tax_rate(db, payload.get("tax_rate"))
    prefix = _customer_quote_prefix()
    seq = await repo.next_customer_quote_sequence(db, prefix)
    quote_no = f"{prefix}{seq:03d}"

    first_machine_id = machine_lines[0].get("machine_id")
    header_machine_id = first_machine_id or await repo.get_generic_machine_id(db)

    quote = await repo.create_quote(
        db,
        {
            "quote_no": quote_no,
            "title": payload["title"],
            "customer_id": payload["customer_id"],
            "project_id": payload.get("project_id"),
            "machine_id": header_machine_id,
            "quote_kind": "customer",
            "tax_rate": tax_rate,
            "currency": payload.get("currency", "CNY"),
            "valid_until": payload.get("valid_until"),
            "remark": payload.get("remark"),
            "total_amount": Decimal("0"),
            "current_approval_order": 0,
            "workflow_state": "draft",
            "created_by": current_user.id,
        },
        autocommit=False,
    )

    items_payload = _machine_lines_to_items(machine_lines)
    subtotal = Decimal("0")
    for item in items_payload:
        subtotal += item["quantity"] * item["unit_price"]

    next_version = 1
    await repo.mark_other_versions_not_current(db, quote.id)
    version = await repo.create_quote_version(
        db,
        {
            "quote_id": quote.id,
            "version_no": next_version,
            "bom_snapshot": None,
            "cost_snapshot": None,
            "analysis_snapshot": {},
            "total_amount": Decimal("0"),
            "total_cost": Decimal("0"),
            "profit_amount": Decimal("0"),
            "profit_rate": Decimal("0"),
            "is_current": True,
            "changed_at": datetime.now(UTC),
            "created_by": current_user.id,
        },
        autocommit=False,
    )

    for item in items_payload:
        qty = item["quantity"]
        price = item["unit_price"]
        line_total = qty * price
        await repo.create_quote_item(
            db,
            {
                "quote_version_id": version.id,
                **item,
                "line_total": line_total,
                "created_by": current_user.id,
            },
            autocommit=False,
        )

    await _apply_customer_quote_totals(db, quote, version, tax_rate=tax_rate, subtotal=subtotal)
    await db.commit()
    return await get_quote_detail(db, quote.id, current_user)


async def update_customer_quote(db: AsyncSession, quote_id: UUID, payload: dict, current_user):
    quote = await repo.get_quote(db, quote_id)
    if quote is None or quote.quote_kind != "customer":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer quote not found")
    if quote.receivable_status == "posted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已生成应收的报价不可修改，请先作废对应应收账目")

    header_updates = {k: v for k, v in payload.items() if k in {"title", "customer_id", "project_id", "currency", "valid_until", "remark"} and v is not None}
    if header_updates:
        await repo.update_quote(db, quote, header_updates, autocommit=False)

    if payload.get("machine_lines") is not None:
        tax_rate = await _resolve_tax_rate(db, payload.get("tax_rate") if payload.get("tax_rate") is not None else float(quote.tax_rate or 0))
        items_payload = _machine_lines_to_items(payload["machine_lines"])
        subtotal = sum((i["quantity"] * i["unit_price"] for i in items_payload), Decimal("0"))
        next_version = await repo.max_quote_version_no(db, quote.id) + 1
        await repo.mark_other_versions_not_current(db, quote.id)
        version = await repo.create_quote_version(
            db,
            {
                "quote_id": quote.id,
                "version_no": next_version,
                "bom_snapshot": None,
                "cost_snapshot": None,
                "analysis_snapshot": {},
                "total_amount": Decimal("0"),
                "total_cost": Decimal("0"),
                "profit_amount": Decimal("0"),
                "profit_rate": Decimal("0"),
                "is_current": True,
                "changed_at": datetime.now(UTC),
                "created_by": current_user.id,
            },
            autocommit=False,
        )
        for item in items_payload:
            qty = item["quantity"]
            price = item["unit_price"]
            await repo.create_quote_item(
                db,
                {
                    "quote_version_id": version.id,
                    **item,
                    "line_total": qty * price,
                    "created_by": current_user.id,
                },
                autocommit=False,
            )
        first_machine_id = payload["machine_lines"][0].get("machine_id") if payload["machine_lines"] else None
        if first_machine_id:
            quote.machine_id = first_machine_id
        await _apply_customer_quote_totals(db, quote, version, tax_rate=tax_rate, subtotal=subtotal)
    elif payload.get("tax_rate") is not None:
        current_version = await repo.get_current_quote_version(db, quote.id)
        if current_version:
            subtotal = Decimal(str(current_version.total_amount or 0))
            tax_rate = await _resolve_tax_rate(db, payload.get("tax_rate"))
            await _apply_customer_quote_totals(db, quote, current_version, tax_rate=tax_rate, subtotal=subtotal)

    await db.commit()
    return await get_quote_detail(db, quote.id, current_user)


async def delete_customer_quote(db: AsyncSession, quote_id: UUID, current_user):
    quote = await repo.get_quote(db, quote_id, predicate=scope_predicate(Quote, current_user))
    if quote is None or quote.quote_kind != "customer":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer quote not found")
    await repo.soft_delete_quote(db, quote, autocommit=True)
    return QuoteRead.model_validate(quote)


async def current_approval_node(db: AsyncSession, quote) -> object | None:
    if not quote.approval_template_id:
        return None
    nodes = await repo.list_approval_nodes(db, quote.approval_template_id)
    if not nodes:
        return None
    if quote.current_approval_order == 0:
        return nodes[0]
    for node in nodes:
        if node.node_order == quote.current_approval_order:
            return node
    return None
