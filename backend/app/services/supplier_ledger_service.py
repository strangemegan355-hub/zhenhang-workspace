from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier
from app.models.supplier_ledger_account import SupplierLedgerAccount
from app.models.accounting_entry import AccountingEntry
from app.models.accounting_settlement import AccountingSettlement
from app.core.data_scope import scope_predicate
from app.models.user import User
from app.repositories import accounting_repository as repo
from app.schemas.accounting import (
    LedgerEntryRead,
    LedgerSupplierRegisterPayload,
    LedgerPayableCreatePayload,
    PaymentCreatePayload,
    PaymentAllocationItem,
    SupplierLedgerDetailRead,
    SupplierLedgerSummaryRead,
)
from app.schemas.common import PageResponse
from app.services import accounting_service as acct_svc

_PAYABLE = "payable"
_PAYMENT = "payment"

_SOURCE_TYPE_LABELS = {
    "manual": "手录账目",
    "procurement": "采购",
}


async def _require_accounting(db: AsyncSession) -> None:
    await acct_svc.require_accounting_enabled(db)


async def _ensure_supplier_accessible(db: AsyncSession, supplier_id: UUID) -> Supplier:
    from sqlalchemy import select

    supplier = (await db.execute(
        select(Supplier).where(Supplier.id == supplier_id, Supplier.is_deleted.is_(False))
    )).scalar_one_or_none()
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


def _to_ledger_entry(e: AccountingEntry) -> LedgerEntryRead:
    open_amount = max(Decimal("0"), Decimal(str(e.amount or 0)) - Decimal(str(e.settled_amount or 0)))
    return LedgerEntryRead(
        id=e.id,
        entry_no=e.entry_no,
        entry_kind=e.entry_kind,
        status=e.status,
        customer_id=None,
        amount=Decimal(str(e.amount or 0)),
        settled_amount=Decimal(str(e.settled_amount or 0)),
        open_amount=open_amount,
        payment_status=(
            "settled" if open_amount == 0 else ("partial" if Decimal(str(e.settled_amount or 0)) > 0 else "unpaid")
        ),
        source_type=e.source_type or "manual",
        source_label=_SOURCE_TYPE_LABELS.get(e.source_type or "", "手录账目"),
        source_no=e.source_no,
        quote_id=None,
        occurred_on=e.occurred_on,
        title=e.title,
        remark=e.remark,
        is_backfill=bool(e.is_backfill),
        allocations=[],
    )


async def register_supplier(
    db: AsyncSession,
    payload: LedgerSupplierRegisterPayload,
    current_user_id: UUID,
) -> SupplierLedgerAccount:
    await _require_accounting(db)
    await _ensure_supplier_accessible(db, payload.supplier_id)
    return await repo.register_supplier_ledger_account(db, payload.supplier_id, current_user_id)


async def get_supplier_ledger_summaries(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    outstanding_only: bool = False,
    q: str | None = None,
    current_user: User,
) -> PageResponse:
    await _require_accounting(db)
    rows = await repo.supplier_ledger_rows(db, predicate=scope_predicate(AccountingEntry, current_user))
    # rows: list of (Supplier, list of confirmed payables, is_registered)
    summaries: list[SupplierLedgerSummaryRead] = []
    for supplier, payables, registered in rows:
        payable_total = Decimal("0")
        paid_total = Decimal("0")
        for p in payables:
            amt = Decimal(str(p.amount or 0))
            settled = Decimal(str(p.settled_amount or 0))
            payable_total += amt
            paid_total += settled
        outstanding = payable_total - paid_total
        if outstanding_only and outstanding <= 0:
            continue
        if q:
            q_lower = q.lower()
            name = (supplier.name or "").lower()
            code = (supplier.code or "").lower()
            if q_lower not in name and q_lower not in code:
                continue
        summaries.append(SupplierLedgerSummaryRead(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            supplier_code=supplier.code,
            payable_total=payable_total,
            paid_total=paid_total,
            outstanding_total=outstanding,
            open_bill_count=len([p for p in payables if Decimal(str(p.amount or 0)) - Decimal(str(p.settled_amount or 0)) > 0]),
            last_occurred_on=max((p.occurred_on for p in payables), default=None),
            is_registered=registered,
        ))
    # paginate
    total = len(summaries)
    start = (page - 1) * page_size
    end = start + page_size
    return PageResponse(total=total, page=page, page_size=page_size, items=summaries[start:end])


async def get_supplier_ledger_detail(
    db: AsyncSession, supplier_id: UUID, current_user: User
) -> SupplierLedgerDetailRead:
    await _require_accounting(db)
    supplier = await _ensure_supplier_accessible(db, supplier_id)
    acct = await repo.get_supplier_ledger_account(db, supplier_id)
    is_registered = acct is not None

    entries = await repo.list_supplier_ledger_entries(
        db,
        supplier_id,
        entry_kinds=(_PAYABLE, _PAYMENT),
        predicate=scope_predicate(AccountingEntry, current_user),
    )

    payable_total = Decimal("0")
    paid_total = Decimal("0")
    for e in entries:
        amt = Decimal(str(e.amount or 0))
        settled = Decimal(str(e.settled_amount or 0))
        if e.entry_kind == _PAYABLE:
            payable_total += amt
            paid_total += settled
        # payments already counted against payables via settled_amount

    return SupplierLedgerDetailRead(
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        supplier_code=supplier.code,
        is_registered=is_registered,
        payable_total=payable_total,
        paid_total=paid_total,
        outstanding_total=payable_total - paid_total,
        entries=[_to_ledger_entry(e) for e in entries],
    )


async def create_manual_payable(
    db: AsyncSession,
    supplier_id: UUID,
    payload: LedgerPayableCreatePayload,
    current_user: User,
) -> LedgerEntryRead:
    await _require_accounting(db)
    await _ensure_supplier_accessible(db, supplier_id)
    if payload.is_backfill:
        # ponytail: backfill permission check — reuse accounting service's check
        pass

    obj = await repo.create_entry(db, {
        "entry_no": await repo.generate_entry_no(db, _PAYABLE),
        "entry_kind": _PAYABLE,
        "status": "confirmed",
        "party_type": "supplier",
        "customer_id": None,
        "supplier_id": supplier_id,
        "project_id": None,
        "amount": Decimal(str(payload.amount)),
        "settled_amount": Decimal("0"),
        "currency": "CNY",
        "occurred_on": payload.occurred_on,
        "due_date": payload.due_date,
        "booked_on": date.today(),
        "is_backfill": payload.is_backfill,
        "source_type": "manual",
        "approval_status": "none",
        "title": payload.title.strip(),
        "remark": payload.remark.strip() if payload.remark else None,
        "created_by": current_user.id,
    })
    scope = scope_predicate(AccountingEntry, current_user)
    loaded = await repo.get_entry(db, obj.id, predicate=scope)
    entry = loaded or obj
    return _to_ledger_entry(entry)


async def create_payment_with_allocations(
    db: AsyncSession,
    payload: PaymentCreatePayload,
    current_user: User,
) -> LedgerEntryRead:
    await _require_accounting(db)
    await _ensure_supplier_accessible(db, payload.supplier_id)

    # Validate allocations
    scope = scope_predicate(AccountingEntry, current_user)
    total_allocated = Decimal("0")
    for alloc in payload.allocations:
        pay = await repo.get_entry(db, alloc.payable_entry_id, predicate=scope)
        if pay is None or pay.entry_kind != _PAYABLE or pay.supplier_id != payload.supplier_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid payable: {alloc.payable_entry_id}")
        if pay.status != "confirmed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Payable not confirmed: {alloc.payable_entry_id}")
        open_amt = Decimal(str(pay.amount or 0)) - Decimal(str(pay.settled_amount or 0))
        if alloc.amount > open_amt:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Overpayment: {alloc.payable_entry_id}")
        total_allocated += alloc.amount

    if abs(total_allocated - Decimal(str(payload.amount))) > Decimal("0.01"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分配金额合计与付款金额不一致")

    # Create payment entry
    payment = await repo.create_entry(db, {
        "entry_no": await repo.generate_entry_no(db, _PAYMENT),
        "entry_kind": _PAYMENT,
        "status": "confirmed",
        "party_type": "supplier",
        "customer_id": None,
        "supplier_id": payload.supplier_id,
        "project_id": None,
        "amount": Decimal(str(payload.amount)),
        "settled_amount": Decimal("0"),
        "currency": "CNY",
        "occurred_on": payload.occurred_on,
        "due_date": None,
        "booked_on": date.today(),
        "is_backfill": False,
        "source_type": "manual",
        "approval_status": "none",
        "title": payload.title.strip(),
        "remark": payload.remark.strip() if payload.remark else None,
        "created_by": current_user.id,
    })

    # Create settlements and update payable settled amounts
    for alloc in payload.allocations:
        await repo.create_settlement(db, {
            "receipt_entry_id": payment.id,  # payment acts as "receipt" in settlement table
            "receivable_entry_id": alloc.payable_entry_id,
            "amount": alloc.amount,
            "party_type": "supplier",
        })
        pay = await repo.get_entry(db, alloc.payable_entry_id, predicate=scope)
        if pay:
            pay.settled_amount = Decimal(str(pay.settled_amount or 0)) + alloc.amount
            await repo.save_entry(db, pay)

    loaded = await repo.get_entry(db, payment.id, predicate=scope)
    entry = loaded or payment
    result = _to_ledger_entry(entry)
    # load allocations for display
    settlements = await repo.list_settlements_by_receipt(db, payment.id, predicate=scope)
    result.allocations = [
        {"receivable_entry_id": str(s.receivable_entry_id), "amount": str(s.amount)}
        for s in settlements
    ]
    return result
