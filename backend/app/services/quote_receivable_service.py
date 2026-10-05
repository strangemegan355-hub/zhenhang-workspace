from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.quote.repositories import quote_repository as quote_repo
from app.models.permission import Permission
from app.models.quote import Quote
from app.models.role import Role
from app.models.user import User
from app.notifications.notification_service import create_notification
from app.repositories import accounting_repository as accounting_repo
from app.repositories import quote_receivable_repository as qrr_repo
from app.repositories.product_repository import get_product
from app.schemas.accounting import AccountingEntryRead, QuoteReceivableRequestRead
from app.schemas.common import PageResponse
from app.services.accounting_service import require_accounting_enabled
from app.services.business_settings_service import get_business_settings_dict


async def _require_quote_receivable_enabled(db: AsyncSession) -> None:
    flags = await require_accounting_enabled(db)
    if not flags.quote_receivable_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="对客报价生成应收未开启，请在业务设置中启用 quote_receivable_enabled",
        )


async def _load_customer_quote(db: AsyncSession, quote_id: UUID) -> tuple[Quote, object, list]:
    quote = await quote_repo.get_quote(db, quote_id)
    if quote is None or quote.quote_kind != "customer":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer quote not found")
    if quote.receivable_status == "posted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该报价已生成应收，不可重复申请")
    existing_entry = await accounting_repo.get_entry_by_quote_source(db, quote_id)
    if existing_entry is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该报价已有有效应收账目")

    active = await qrr_repo.get_active_request_by_quote(db, quote_id)
    if active is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该报价已有进行中的应收申请")

    version = await quote_repo.get_current_quote_version(db, quote_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="报价无有效版本")
    items = await quote_repo.list_quote_items_by_version(db, version.id)
    if not items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="报价无明细行")
    return quote, version, items


async def _compute_amounts(db: AsyncSession, quote: Quote, items: list) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    subtotal_std = Decimal("0")
    subtotal_actual = Decimal("0")
    for item in items:
        qty = Decimal(str(item.quantity))
        unit_price = Decimal(str(item.unit_price))
        subtotal_actual += qty * unit_price
        ref_price = unit_price
        if item.product_id:
            product = await get_product(db, item.product_id)
            if product is not None:
                ref_price = Decimal(str(product.reference_price or unit_price))
        subtotal_std += qty * ref_price

    tax_rate = Decimal(str(quote.tax_rate or 0))
    std_tax = (subtotal_std * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
    standard_amount = (subtotal_std + std_tax).quantize(Decimal("0.01"))
    requested_amount = Decimal(str(quote.total_amount or 0)).quantize(Decimal("0.01"))
    discount_amount = max(Decimal("0"), (standard_amount - requested_amount).quantize(Decimal("0.01")))
    discount_rate_pct = (
        Decimal("0")
        if standard_amount <= 0
        else (discount_amount / standard_amount * Decimal("100")).quantize(Decimal("0.01"))
    )
    return standard_amount, requested_amount, discount_amount, discount_rate_pct


async def _notify_bosses(db: AsyncSession, *, title: str, content: str, biz_id: UUID, created_by: UUID | None) -> None:
    perm_stmt = (
        select(User.id)
        .join(User.roles)
        .join(Role.permissions)
        .where(
            User.is_active.is_(True),
            Permission.code == "business:accounting:approve_quote_receivable",
        )
        .distinct()
    )
    super_stmt = select(User.id).where(User.is_active.is_(True), User.is_superuser.is_(True))
    boss_ids = set((await db.execute(perm_stmt)).scalars().all())
    boss_ids.update((await db.execute(super_stmt)).scalars().all())
    for boss_id in boss_ids:
        await create_notification(
            db,
            title=title,
            content=content,
            biz_type="quote_receivable_request",
            biz_id=biz_id,
            receiver_id=boss_id,
            payload={"quote_id": str(biz_id)},
            created_by=created_by,
            autocommit=False,
        )


async def create_request_from_quote(db: AsyncSession, quote_id: UUID, current_user: User) -> QuoteReceivableRequestRead:
    await _require_quote_receivable_enabled(db)
    quote, _version, items = await _load_customer_quote(db, quote_id)
    standard_amount, requested_amount, discount_amount, discount_rate_pct = await _compute_amounts(db, quote, items)
    settings = await get_business_settings_dict(db)
    max_sales_discount = Decimal(str(settings.get("sales_max_discount_rate_pct", 0)))
    needs_boss = discount_amount > 0 and discount_rate_pct > max_sales_discount
    approval_status = "pending" if needs_boss else "approved"

    obj = await qrr_repo.create_request(
        db,
        {
            "quote_id": quote_id,
            "requested_by": current_user.id,
            "requested_amount": requested_amount,
            "standard_amount": standard_amount,
            "discount_amount": discount_amount,
            "discount_rate_pct": discount_rate_pct,
            "needs_boss_approval": needs_boss,
            "approval_status": approval_status,
            "created_by": current_user.id,
        },
    )
    quote.receivable_status = "pending" if needs_boss else "approved"
    await db.flush()

    if needs_boss:
        await _notify_bosses(
            db,
            title=f"应收优惠待审批 · {quote.quote_no}",
            content=f"报价 {quote.title} 含优惠 {discount_amount} 元，请审批后销售方可确认应收。",
            biz_id=obj.id,
            created_by=current_user.id,
        )

    await qrr_repo.commit_session(db)
    loaded = await qrr_repo.get_request(db, obj.id)
    return QuoteReceivableRequestRead.model_validate(loaded or obj)


async def list_requests(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    approval_status: str | None = None,
    quote_id: UUID | None = None,
) -> PageResponse:
    await require_accounting_enabled(db)
    total, items = await qrr_repo.list_requests(
        db,
        page=page,
        page_size=page_size,
        approval_status=approval_status,
        quote_id=quote_id,
    )
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[QuoteReceivableRequestRead.model_validate(i) for i in items],
    )


async def get_request_for_quote(db: AsyncSession, quote_id: UUID) -> QuoteReceivableRequestRead | None:
    await require_accounting_enabled(db)
    obj = await qrr_repo.get_active_request_by_quote(db, quote_id)
    if obj is None:
        posted = await accounting_repo.get_entry_by_quote_source(db, quote_id)
        if posted is not None:
            return None
        return None
    return QuoteReceivableRequestRead.model_validate(obj)


async def approve_request(db: AsyncSession, request_id: UUID, current_user: User) -> QuoteReceivableRequestRead:
    await _require_quote_receivable_enabled(db)
    obj = await qrr_repo.get_request(db, request_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="应收申请不存在")
    if obj.approval_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅待审批申请可通过")
    obj.approval_status = "approved"
    obj.approved_by = current_user.id
    obj.approved_at = datetime.now(UTC)
    if obj.quote:
        obj.quote.receivable_status = "approved"
    await qrr_repo.save_request(db, obj)
    loaded = await qrr_repo.get_request(db, request_id)
    return QuoteReceivableRequestRead.model_validate(loaded or obj)


async def reject_request(
    db: AsyncSession,
    request_id: UUID,
    current_user: User,
    *,
    reason: str | None,
) -> QuoteReceivableRequestRead:
    await _require_quote_receivable_enabled(db)
    obj = await qrr_repo.get_request(db, request_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="应收申请不存在")
    if obj.approval_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅待审批申请可驳回")
    obj.approval_status = "rejected"
    obj.approved_by = current_user.id
    obj.approved_at = datetime.now(UTC)
    obj.reject_reason = reason.strip() if reason else None
    if obj.quote:
        obj.quote.receivable_status = "none"
    await qrr_repo.save_request(db, obj)
    loaded = await qrr_repo.get_request(db, request_id)
    return QuoteReceivableRequestRead.model_validate(loaded or obj)


async def confirm_receivable(db: AsyncSession, request_id: UUID, current_user: User) -> AccountingEntryRead:
    await _require_quote_receivable_enabled(db)
    obj = await qrr_repo.get_request(db, request_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="应收申请不存在")
    if obj.receivable_entry_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="应收已确认")
    if obj.approval_status not in {"approved", "none"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="优惠申请尚未通过审批")

    quote = obj.quote or await quote_repo.get_quote(db, obj.quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer quote not found")

    version = await quote_repo.get_current_quote_version(db, quote.id)
    items = await quote_repo.list_quote_items_by_version(db, version.id) if version else []

    today = date.today()
    entry = await accounting_repo.create_entry_with_lines(
        db,
        {
            "entry_no": await accounting_repo.generate_entry_no(db, "receivable"),
            "entry_kind": "receivable",
            "status": "confirmed",
            "party_type": "customer",
            "customer_id": quote.customer_id,
            "supplier_id": None,
            "project_id": quote.project_id,
            "quote_id": quote.id,
            "amount": Decimal(str(obj.requested_amount)),
            "settled_amount": Decimal("0"),
            "currency": quote.currency or "CNY",
            "occurred_on": today,
            "booked_on": today,
            "is_backfill": False,
            "source_type": "customer_quote",
            "source_id": quote.id,
            "source_no": quote.quote_no,
            "approval_status": "approved" if obj.needs_boss_approval else "none",
            "title": f"对客报价应收 · {quote.quote_no}",
            "remark": quote.remark,
            "created_by": current_user.id,
        },
        [
            {
                "product_id": item.product_id,
                "item_name": item.item_name,
                "spec": item.spec,
                "unit": item.unit,
                "qty": Decimal(str(item.quantity)),
                "unit_price": Decimal(str(item.unit_price)),
                "line_amount": Decimal(str(item.line_total)),
                "created_by": current_user.id,
            }
            for item in items
        ],
    )

    obj.receivable_entry_id = entry.id
    quote.receivable_status = "posted"
    await db.flush()
    await qrr_repo.commit_session(db)

    loaded = await accounting_repo.get_entry(db, entry.id)
    return AccountingEntryRead.model_validate(loaded or entry)
