from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import scope_predicate
from app.models.accounting_entry import AccountingEntry
from app.models.user import User
from app.repositories import accounting_repository as repo
from app.repositories import customer_repository as customer_repo
from app.schemas.accounting import (
    SOURCE_TYPE_LABELS,
    AccountingEntryRead,
    CustomerLedgerSummaryRead,
    LedgerEntryRead,
    LedgerReceivableCreatePayload,
    ReceiptCreatePayload,
)
from app.schemas.common import PageResponse
from app.services.accounting_service import _validate_dates, require_accounting_enabled


def _payment_status(amount: Decimal, settled: Decimal) -> str:
    if settled <= 0:
        return "unpaid"
    if settled >= amount:
        return "paid"
    return "partial"


def _source_label(source_type: str) -> str:
    return SOURCE_TYPE_LABELS.get(source_type, source_type)


def _to_ledger_receivable(entry) -> LedgerEntryRead:
    amount = Decimal(str(entry.amount or 0))
    settled = Decimal(str(entry.settled_amount or 0))
    open_amount = max(Decimal("0"), amount - settled)
    ps = _payment_status(amount, settled)
    return LedgerEntryRead(
        id=entry.id,
        entry_no=entry.entry_no,
        entry_kind=entry.entry_kind,
        status=entry.status,
        customer_id=entry.customer_id,
        amount=amount,
        settled_amount=settled,
        open_amount=open_amount,
        payment_status=ps,
        source_type=entry.source_type,
        source_label=_source_label(entry.source_type),
        source_no=entry.source_no,
        quote_id=entry.quote_id,
        occurred_on=entry.occurred_on,
        title=entry.title,
        remark=entry.remark,
        is_backfill=entry.is_backfill,
        allocations=[],
    )


def _summarize_customer(customer, receivables: list, *, is_registered: bool = False) -> CustomerLedgerSummaryRead:
    receivable_total = Decimal("0")
    received_total = Decimal("0")
    outstanding_total = Decimal("0")
    open_bill_count = 0
    last_date: date | None = None

    for r in receivables:
        amount = Decimal(str(r.amount or 0))
        settled = Decimal(str(r.settled_amount or 0))
        open_amt = max(Decimal("0"), amount - settled)
        receivable_total += amount
        received_total += settled
        outstanding_total += open_amt
        if open_amt > 0:
            open_bill_count += 1
        if last_date is None or r.occurred_on > last_date:
            last_date = r.occurred_on

    return CustomerLedgerSummaryRead(
        customer_id=customer.id,
        customer_name=customer.name,
        customer_code=customer.code,
        receivable_total=receivable_total,
        received_total=received_total,
        outstanding_total=outstanding_total,
        open_bill_count=open_bill_count,
        last_occurred_on=last_date,
        is_registered=is_registered,
    )


async def list_customer_summaries(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    outstanding_only: bool = False,
    q: str | None = None,
    current_user: User,
) -> PageResponse:
    await require_accounting_enabled(db)
    rows = await repo.customer_ledger_rows(db, predicate=scope_predicate(AccountingEntry, current_user))
    summaries: list[CustomerLedgerSummaryRead] = []
    for customer, receivables, is_registered in rows:
        summary = _summarize_customer(customer, receivables, is_registered=is_registered)
        if outstanding_only and summary.outstanding_total <= 0:
            continue
        if q:
            key = q.strip().lower()
            if key not in summary.customer_name.lower() and key not in (summary.customer_code or "").lower():
                continue
        summaries.append(summary)

    summaries.sort(key=lambda s: (s.outstanding_total, s.customer_name), reverse=True)
    total = len(summaries)
    start = (page - 1) * page_size
    page_items = summaries[start : start + page_size]
    return PageResponse(total=total, page=page, page_size=page_size, items=page_items)


async def _ensure_customer_accessible(db: AsyncSession, customer_id: UUID, current_user: User):
    customer = await customer_repo.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="客户不存在")
    account = await repo.get_ledger_account(db, customer_id)
    if account is None:
        _, receivables = await _customer_receivables_only(db, customer_id, current_user)
        if not receivables:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="客户未加入账目明细，请先添加")
    return customer


async def _customer_receivables_only(
    db: AsyncSession, customer_id: UUID, current_user: User
) -> tuple[object | None, list]:
    customer = await customer_repo.get_customer(db, customer_id)
    receivables = await repo.list_confirmed_customer_receivables(
        db, customer_id, predicate=scope_predicate(AccountingEntry, current_user)
    )
    return customer, receivables


async def register_customer(db: AsyncSession, customer_id: UUID, current_user: User) -> CustomerLedgerSummaryRead:
    await require_accounting_enabled(db)
    customer = await customer_repo.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="客户不存在")
    await repo.register_ledger_account(db, customer_id, current_user.id)
    receivables = await repo.list_confirmed_customer_receivables(
        db, customer_id, predicate=scope_predicate(AccountingEntry, current_user)
    )
    return _summarize_customer(customer, receivables, is_registered=True)


async def get_customer_ledger_detail(db: AsyncSession, customer_id: UUID, current_user: User) -> dict:
    await require_accounting_enabled(db)
    customer = await _ensure_customer_accessible(db, customer_id, current_user)
    scope = scope_predicate(AccountingEntry, current_user)
    receivables = await repo.list_confirmed_customer_receivables(db, customer_id, predicate=scope)
    receipts = await repo.list_customer_receipts(db, customer_id, predicate=scope)

    receipt_ids = [r.id for r in receipts]
    settlements = await repo.list_settlements_by_receipts(db, receipt_ids)
    settlements_by_receipt: dict[UUID, list] = {}
    for s in settlements:
        settlements_by_receipt.setdefault(s.receipt_entry_id, []).append(s)

    receivable_items = [_to_ledger_receivable(r) for r in receivables]

    receipt_items: list[LedgerEntryRead] = []
    for r in receipts:
        allocs = settlements_by_receipt.get(r.id, [])
        receipt_items.append(
            LedgerEntryRead(
                id=r.id,
                entry_no=r.entry_no,
                entry_kind=r.entry_kind,
                status=r.status,
                customer_id=r.customer_id,
                amount=Decimal(str(r.amount or 0)),
                settled_amount=Decimal(str(r.amount or 0)),
                open_amount=Decimal("0"),
                payment_status=None,
                source_type=r.source_type,
                source_label="收款",
                source_no=r.source_no,
                quote_id=None,
                occurred_on=r.occurred_on,
                title=r.title,
                remark=r.remark,
                is_backfill=r.is_backfill,
                allocations=[
                    {
                        "receivable_entry_id": str(s.receivable_entry_id),
                        "receivable_entry_no": s.receivable_entry.entry_no if s.receivable_entry else None,
                        "amount": str(s.amount),
                    }
                    for s in allocs
                ],
            )
        )

    timeline = receivable_items + receipt_items
    timeline.sort(key=lambda x: (x.occurred_on, x.entry_no), reverse=True)

    receivable_total = sum((i.amount for i in receivable_items), Decimal("0"))
    received_total = sum((i.settled_amount for i in receivable_items), Decimal("0"))
    outstanding_total = sum((i.open_amount for i in receivable_items), Decimal("0"))

    open_receivables = [i for i in receivable_items if i.payment_status in {"unpaid", "partial"}]

    return {
        "customer_id": customer_id,
        "customer_name": customer.name,
        "customer_code": customer.code,
        "receivable_total": receivable_total,
        "received_total": received_total,
        "outstanding_total": outstanding_total,
        "open_bill_count": len(open_receivables),
        "receivables": receivable_items,
        "receipts": receipt_items,
        "timeline": timeline,
        "open_receivables": open_receivables,
    }


async def create_manual_receivable(
    db: AsyncSession,
    customer_id: UUID,
    payload: LedgerReceivableCreatePayload,
    current_user: User,
    *,
    allow_backfill: bool,
) -> AccountingEntryRead:
    await require_accounting_enabled(db)
    if payload.is_backfill and not allow_backfill:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无补录账权限")
    customer = await customer_repo.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="客户不存在")

    booked_on = _validate_dates(payload.occurred_on, is_backfill=payload.is_backfill)

    entry = await repo.add_entry(
        db,
        {
            "entry_no": await repo.generate_entry_no(db, "receivable"),
            "entry_kind": "receivable",
            "status": "confirmed",
            "party_type": "customer",
            "customer_id": customer_id,
            "supplier_id": None,
            "amount": Decimal(str(payload.amount)),
            "settled_amount": Decimal("0"),
            "currency": "CNY",
            "occurred_on": payload.occurred_on,
            "booked_on": booked_on,
            "is_backfill": payload.is_backfill,
            "source_type": "manual",
            "approval_status": "none",
            "title": payload.title.strip(),
            "remark": payload.remark.strip() if payload.remark else None,
            "created_by": current_user.id,
        },
    )
    await repo.save_entry(db, entry)
    # Registered after the entry so the single commit above covers both: registering first committed the
    # account before the entry it exists for. The account is a lazily created container, so its moment does
    # not change the result.
    await repo.register_ledger_account(db, customer_id, current_user.id)
    loaded = await repo.get_entry(db, entry.id, predicate=scope_predicate(AccountingEntry, current_user))
    return AccountingEntryRead.model_validate(loaded or entry)


async def create_receipt_with_allocations(
    db: AsyncSession,
    payload: ReceiptCreatePayload,
    current_user: User,
) -> AccountingEntryRead:
    await require_accounting_enabled(db)
    if payload.occurred_on > date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="业务发生日不能晚于今天")

    alloc_sum = sum((Decimal(str(a.amount)) for a in payload.allocations), Decimal("0"))
    receipt_amount = Decimal(str(payload.amount))
    if alloc_sum != receipt_amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="核销明细合计必须等于收款金额")

    receivable_ids = [a.receivable_entry_id for a in payload.allocations]
    receivables: dict[UUID, object] = {}
    for rid in receivable_ids:
        # Row lock: prevent concurrent receipts from over-settling the same AR.
        obj = await repo.get_entry(
            db,
            rid,
            predicate=scope_predicate(AccountingEntry, current_user),
            for_update=True,
        )
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"应收账目不存在: {rid}")
        if obj.entry_kind != "receivable" or obj.status != "confirmed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"账目 {obj.entry_no} 不是已确认应收")
        if obj.customer_id != payload.customer_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"账目 {obj.entry_no} 不属于该客户")
        receivables[rid] = obj

    for item in payload.allocations:
        obj = receivables[item.receivable_entry_id]
        amount = Decimal(str(obj.amount or 0))
        settled = Decimal(str(obj.settled_amount or 0))
        open_amt = amount - settled
        alloc = Decimal(str(item.amount))
        if alloc <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="核销金额必须大于 0")
        if alloc > open_amt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"账目 {obj.entry_no} 未收余额不足（剩余 {open_amt}）",
            )

    booked_on = date.today()
    receipt = await repo.add_entry(
        db,
        {
            "entry_no": await repo.generate_entry_no(db, "receipt"),
            "entry_kind": "receipt",
            "status": "confirmed",
            "party_type": "customer",
            "customer_id": payload.customer_id,
            "supplier_id": None,
            "amount": receipt_amount,
            "settled_amount": receipt_amount,
            "currency": "CNY",
            "occurred_on": payload.occurred_on,
            "booked_on": booked_on,
            "is_backfill": False,
            "source_type": "manual",
            "approval_status": "none",
            "title": payload.title.strip(),
            "remark": payload.remark.strip() if payload.remark else None,
            "created_by": current_user.id,
        },
    )

    for item in payload.allocations:
        obj = receivables[item.receivable_entry_id]
        alloc = Decimal(str(item.amount))
        obj.settled_amount = Decimal(str(obj.settled_amount or 0)) + alloc
        await repo.create_settlement(
            db,
            {
                "receipt_entry_id": receipt.id,
                "receivable_entry_id": item.receivable_entry_id,
                "amount": alloc,
                "created_by": current_user.id,
            },
        )

    await repo.save_entry(db, receipt)
    loaded = await repo.get_entry(db, receipt.id)
    return AccountingEntryRead.model_validate(loaded or receipt)
