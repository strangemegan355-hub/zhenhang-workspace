from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import scope_predicate
from app.models.accounting_entry import AccountingEntry
from app.models.user import User
from app.repositories import accounting_repository as repo
from app.schemas.accounting import (
    CUSTOMER_KINDS,
    SUPPLIER_KINDS,
    AccountingEntryCreate,
    AccountingEntryRead,
    AccountingFeatureFlags,
    AccountingModuleStatus,
    PostExpensePayload,
)
from app.schemas.common import PageResponse
from app.services.business_settings_service import get_business_settings_dict


def _feature_flags(raw: dict) -> AccountingFeatureFlags:
    return AccountingFeatureFlags(
        accounting_enabled=bool(raw.get("accounting_enabled", False)),
        quote_receivable_enabled=bool(raw.get("quote_receivable_enabled", False)),
        procurement_approval_enabled=bool(raw.get("procurement_approval_enabled", False)),
    )


async def get_feature_flags(db: AsyncSession) -> AccountingFeatureFlags:
    raw = await get_business_settings_dict(db)
    return _feature_flags(raw)


async def require_accounting_enabled(db: AsyncSession) -> AccountingFeatureFlags:
    flags = await get_feature_flags(db)
    if not flags.accounting_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="记账模块未开启，请在业务设置中启用 accounting_enabled",
        )
    return flags


def _validate_dates(occurred_on: date, *, is_backfill: bool) -> date:
    today = date.today()
    if occurred_on > today:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="业务发生日不能晚于今天")
    if is_backfill and occurred_on > today:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="补录日期不能晚于今天")
    return today


def _resolve_party(payload: AccountingEntryCreate) -> tuple[str | None, UUID | None, UUID | None]:
    if payload.entry_kind in CUSTOMER_KINDS:
        if not payload.customer_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该类型账目需选择客户")
        return "customer", payload.customer_id, None
    if payload.entry_kind in SUPPLIER_KINDS:
        if not payload.supplier_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该类型账目需选择供应商")
        return "supplier", None, payload.supplier_id
    return None, payload.customer_id, payload.supplier_id


async def get_module_status(db: AsyncSession) -> AccountingModuleStatus:
    flags = await get_feature_flags(db)
    entry_count = await repo.count_entries(db) if flags.accounting_enabled else 0
    return AccountingModuleStatus(flags=flags, entry_count=entry_count)


async def list_entries(
    db: AsyncSession,
    current_user: User,
    *,
    page: int,
    page_size: int,
    customer_id: UUID | None = None,
    supplier_id: UUID | None = None,
    entry_kind: str | None = None,
    include_void: bool = False,
    date_from: date | None = None,
    date_to: date | None = None,
) -> PageResponse:
    await require_accounting_enabled(db)
    total, items = await repo.list_entries(
        db,
        page=page,
        predicate=scope_predicate(AccountingEntry, current_user),
        page_size=page_size,
        customer_id=customer_id,
        supplier_id=supplier_id,
        entry_kind=entry_kind,
        include_void=include_void,
        date_from=date_from,
        date_to=date_to,
    )
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AccountingEntryRead.model_validate(item) for item in items],
    )


async def get_entry(db: AsyncSession, entry_id: UUID, current_user: User) -> AccountingEntryRead:
    await require_accounting_enabled(db)
    obj = await repo.get_entry(db, entry_id, predicate=scope_predicate(AccountingEntry, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accounting entry not found")
    return AccountingEntryRead.model_validate(obj)


async def create_entry(
    db: AsyncSession,
    payload: AccountingEntryCreate,
    current_user: User,
    *,
    allow_backfill: bool,
) -> AccountingEntryRead:
    await require_accounting_enabled(db)
    if payload.is_backfill and not allow_backfill:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无补录账权限")

    booked_on = _validate_dates(payload.occurred_on, is_backfill=payload.is_backfill)
    party_type, customer_id, supplier_id = _resolve_party(payload)

    obj = await repo.create_entry(
        db,
        {
            "entry_no": await repo.generate_entry_no(db, payload.entry_kind),
            "entry_kind": payload.entry_kind,
            "status": "draft",
            "party_type": party_type,
            "customer_id": customer_id,
            "supplier_id": supplier_id,
            "project_id": payload.project_id,
            "amount": Decimal(str(payload.amount)),
            "settled_amount": Decimal("0"),
            "currency": "CNY",
            "occurred_on": payload.occurred_on,
            "due_date": payload.due_date,
            "booked_on": booked_on,
            "is_backfill": payload.is_backfill,
            "source_type": "manual",
            "approval_status": "none",
            "title": payload.title.strip(),
            "remark": payload.remark.strip() if payload.remark else None,
            "created_by": current_user.id,
        },
    )
    loaded = await repo.get_entry(db, obj.id)
    return AccountingEntryRead.model_validate(loaded or obj)


async def update_entry(
    db: AsyncSession,
    entry_id: UUID,
    payload,
    current_user: User,
) -> AccountingEntryRead:
    await require_accounting_enabled(db)
    obj = await repo.get_entry(db, entry_id, predicate=scope_predicate(AccountingEntry, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accounting entry not found")
    if obj.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅草稿状态可编辑")
    updates = payload.model_dump(exclude_unset=True)
    if "occurred_on" in updates:
        _validate_dates(updates["occurred_on"], is_backfill=bool(obj.is_backfill))
    for key, value in updates.items():
        if value is not None:
            setattr(obj, key, value)
    await repo.save_entry(db, obj)
    loaded = await repo.get_entry(db, entry_id)
    return AccountingEntryRead.model_validate(loaded or obj)


async def confirm_entry(db: AsyncSession, entry_id: UUID, current_user) -> AccountingEntryRead:
    await require_accounting_enabled(db)
    obj = await repo.get_entry(db, entry_id, predicate=scope_predicate(AccountingEntry, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accounting entry not found")
    if obj.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅草稿状态可确认")
    obj.status = "confirmed"
    await repo.save_entry(db, obj)
    loaded = await repo.get_entry(db, entry_id)
    return AccountingEntryRead.model_validate(loaded or obj)


async def void_entry(db: AsyncSession, entry_id: UUID, current_user) -> AccountingEntryRead:
    await require_accounting_enabled(db)
    obj = await repo.get_entry(db, entry_id, predicate=scope_predicate(AccountingEntry, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accounting entry not found")
    if obj.status == "void":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账目已作废")
    if obj.status not in {"draft", "confirmed"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可作废")
    if obj.entry_kind == "receipt":
        settlements = await repo.list_settlements_by_receipt(db, entry_id)
        if settlements:
            for s in settlements:
                recv = await repo.get_entry(db, s.receivable_entry_id)
                if recv is not None:
                    recv.settled_amount = max(
                        Decimal("0"),
                        Decimal(str(recv.settled_amount or 0)) - Decimal(str(s.amount or 0)),
                    )
                s.is_deleted = True
        obj.status = "void"
        await repo.save_entry(db, obj)
        loaded = await repo.get_entry(db, entry_id)
        return AccountingEntryRead.model_validate(loaded or obj)
    if Decimal(str(obj.settled_amount or 0)) > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已有核销金额，不可作废")
    obj.status = "void"
    if obj.source_type == "customer_quote" and obj.quote_id is not None:
        from sqlalchemy import select

        from app.models.quote import Quote
        from app.models.quote_receivable_request import QuoteReceivableRequest

        quote = (await db.execute(select(Quote).where(Quote.id == obj.quote_id))).scalar_one_or_none()
        if quote is not None:
            quote.receivable_status = "none"
        req_rows = (
            await db.execute(
                select(QuoteReceivableRequest).where(
                    QuoteReceivableRequest.quote_id == obj.quote_id,
                    QuoteReceivableRequest.receivable_entry_id == obj.id,
                    QuoteReceivableRequest.is_deleted.is_(False),
                )
            )
        ).scalars().all()
        for req in req_rows:
            req.receivable_entry_id = None
            req.approval_status = "rejected"
            req.reject_reason = "关联应收账目已作废"
    if obj.source_type == "fieldwork_repair" and obj.source_id is not None:
        from app.models.fieldwork_record import FieldworkRecord

        fw = (await db.execute(select(FieldworkRecord).where(FieldworkRecord.id == obj.source_id))).scalar_one_or_none()
        if fw is not None and fw.receivable_entry_id == obj.id:
            fw.receivable_entry_id = None
    if obj.source_type == "procurement" and obj.source_id is not None:
        from app.models.procurement_entry import ProcurementEntry

        pe = (await db.execute(select(ProcurementEntry).where(ProcurementEntry.id == obj.source_id))).scalar_one_or_none()
        if pe is not None:
            pe.payable_status = "none"
        from app.models.procurement_payable_request import ProcurementPayableRequest

        req_rows = (
            await db.execute(
                select(ProcurementPayableRequest).where(
                    ProcurementPayableRequest.procurement_entry_id == obj.source_id,
                    ProcurementPayableRequest.payable_entry_id == obj.id,
                    ProcurementPayableRequest.is_deleted.is_(False),
                )
            )
        ).scalars().all()
        for req in req_rows:
            req.payable_entry_id = None
            req.approval_status = "rejected"
            req.reject_reason = "关联应付账目已作废"
    await repo.save_entry(db, obj)
    loaded = await repo.get_entry(db, entry_id)
    return AccountingEntryRead.model_validate(loaded or obj)


async def post_source_expense(
    db: AsyncSession,
    *,
    source_type: str,
    source_id: UUID,
    source_no: str,
    amount: Decimal,
    title: str,
    remark: str | None,
    created_by: UUID,
    customer_id: UUID | None = None,
    project_id: UUID | None = None,
) -> AccountingEntryRead:
    """Post a confirmed expense entry for a business object.

    This is the single implementation of what two endpoints used to do inline in near-identical
    copies. `create_entry` is deliberately not reused: it writes a draft, resolves the party from the
    payload and validates backfill dates, whereas these paths post a confirmed entry straight away.
    """
    await require_accounting_enabled(db)
    obj = await repo.create_entry(
        db,
        {
            "entry_no": await repo.generate_entry_no(db, "expense"),
            "entry_kind": "expense",
            "status": "confirmed",
            "party_type": None,
            "customer_id": customer_id,
            "supplier_id": None,
            "project_id": project_id,
            "amount": Decimal(str(amount)),
            "settled_amount": Decimal("0"),
            "currency": "CNY",
            "occurred_on": date.today(),
            "due_date": None,
            "booked_on": date.today(),
            "is_backfill": False,
            "source_type": source_type,
            "source_id": source_id,
            "source_no": source_no,
            "approval_status": "none",
            "title": title.strip(),
            "remark": remark.strip() if remark else None,
            "created_by": created_by,
        },
    )
    loaded = await repo.get_entry(db, obj.id)
    return AccountingEntryRead.model_validate(loaded or obj)


async def post_work_order_expense(
    db: AsyncSession,
    work_order_id: UUID,
    payload: PostExpensePayload,
    current_user: User,
) -> AccountingEntryRead:
    from app.repositories import work_order_repository as wo_repo

    work_order = await wo_repo.get_work_order(db, work_order_id)
    if work_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")
    return await post_source_expense(
        db,
        source_type="work_order",
        source_id=work_order_id,
        source_no=work_order.work_order_no,
        customer_id=work_order.customer_id,
        project_id=work_order.project_id,
        amount=payload.amount,
        title=payload.title,
        remark=payload.remark,
        created_by=current_user.id,
    )


async def post_cost_estimate_expense(
    db: AsyncSession,
    estimate_id: UUID,
    payload: PostExpensePayload,
    current_user: User,
) -> AccountingEntryRead:
    from app.repositories import cost_estimate_repository as est_repo

    estimate = await est_repo.get_cost_estimate(db, estimate_id)
    if estimate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost estimate not found")
    return await post_source_expense(
        db,
        source_type="cost_estimate",
        source_id=estimate_id,
        source_no=estimate.estimate_no,
        amount=payload.amount,
        title=payload.title,
        remark=payload.remark,
        created_by=current_user.id,
    )
