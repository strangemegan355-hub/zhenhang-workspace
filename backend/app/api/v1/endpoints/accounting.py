import csv
from datetime import date
from io import StringIO
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.core.rbac import collect_permission_codes
from app.db.session import get_db
from app.models.user import User
from app.schemas.accounting import (
    AccountingEntryCreate,
    AccountingEntryRead,
    AccountingModuleStatus,
    CustomerLedgerSummaryRead,
    ProcurementPayableRejectPayload,
    ProcurementPayableRequestRead,
    QuoteReceivableRejectPayload,
    QuoteReceivableRequestRead,
    ReceiptCreatePayload,
    LedgerCustomerRegisterPayload,
    LedgerReceivableCreatePayload,
)
from app.schemas.common import PageResponse
from app.services import accounting_service as svc
from app.services import ledger_service as ledger_svc
from app.services import procurement_payable_service as ppr_svc
from app.services import quote_receivable_service as qrr_svc

router = APIRouter()


def _can_backfill(user: User) -> bool:
    if user.is_superuser:
        return True
    perms = collect_permission_codes(user)
    return "business:accounting:backfill" in perms or "*:*:*" in perms


@router.get("/status", response_model=AccountingModuleStatus)
async def get_accounting_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:read"))],
) -> AccountingModuleStatus:
    return await svc.get_module_status(db)


@router.get("/entries", response_model=PageResponse)
async def list_accounting_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    customer_id: UUID | None = Query(default=None),
    supplier_id: UUID | None = Query(default=None),
    entry_kind: str | None = Query(default=None, max_length=32),
    include_void: bool = Query(default=False),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> PageResponse:
    return await svc.list_entries(
        db,
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        supplier_id=supplier_id,
        entry_kind=entry_kind,
        include_void=include_void,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/entries/{entry_id}", response_model=AccountingEntryRead)
async def get_accounting_entry(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:read"))],
) -> AccountingEntryRead:
    return await svc.get_entry(db, entry_id)


@router.post("/entries", response_model=AccountingEntryRead, status_code=status.HTTP_201_CREATED)
async def create_accounting_entry(
    payload: AccountingEntryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:create"))],
) -> AccountingEntryRead:
    return await svc.create_entry(db, payload, current, allow_backfill=_can_backfill(current))


@router.post("/entries/backfill", response_model=AccountingEntryRead, status_code=status.HTTP_201_CREATED)
async def create_backfill_entry(
    payload: AccountingEntryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:backfill"))],
) -> AccountingEntryRead:
    data = payload.model_copy(update={"is_backfill": True})
    return await svc.create_entry(db, data, current, allow_backfill=True)


@router.post("/entries/{entry_id}/confirm", response_model=AccountingEntryRead)
async def confirm_accounting_entry(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:confirm"))],
) -> AccountingEntryRead:
    return await svc.confirm_entry(db, entry_id)


@router.post("/entries/{entry_id}/void", response_model=AccountingEntryRead)
async def void_accounting_entry(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:confirm"))],
) -> AccountingEntryRead:
    return await svc.void_entry(db, entry_id)


@router.post("/quote-receivable-requests/from-quote/{quote_id}", response_model=QuoteReceivableRequestRead, status_code=status.HTTP_201_CREATED)
async def create_quote_receivable_request(
    quote_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:post_quote"))],
) -> QuoteReceivableRequestRead:
    return await qrr_svc.create_request_from_quote(db, quote_id, current)


@router.get("/quote-receivable-requests", response_model=PageResponse)
async def list_quote_receivable_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    approval_status: str | None = Query(default=None, max_length=32),
    quote_id: UUID | None = Query(default=None),
) -> PageResponse:
    return await qrr_svc.list_requests(
        db,
        page=page,
        page_size=page_size,
        approval_status=approval_status,
        quote_id=quote_id,
    )


@router.get("/quote-receivable-requests/by-quote/{quote_id}", response_model=QuoteReceivableRequestRead | None)
async def get_quote_receivable_request_by_quote(
    quote_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:read"))],
) -> QuoteReceivableRequestRead | None:
    return await qrr_svc.get_request_for_quote(db, quote_id)


@router.post("/quote-receivable-requests/{request_id}/approve", response_model=QuoteReceivableRequestRead)
async def approve_quote_receivable_request(
    request_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:approve_quote_receivable"))],
) -> QuoteReceivableRequestRead:
    return await qrr_svc.approve_request(db, request_id, current)


@router.post("/quote-receivable-requests/{request_id}/reject", response_model=QuoteReceivableRequestRead)
async def reject_quote_receivable_request(
    request_id: UUID,
    payload: QuoteReceivableRejectPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:approve_quote_receivable"))],
) -> QuoteReceivableRequestRead:
    return await qrr_svc.reject_request(db, request_id, current, reason=payload.reason)


@router.post("/quote-receivable-requests/{request_id}/confirm", response_model=AccountingEntryRead)
async def confirm_quote_receivable(
    request_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:confirm_receivable"))],
) -> AccountingEntryRead:
    return await qrr_svc.confirm_receivable(db, request_id, current)


@router.post("/ledger/customers", response_model=CustomerLedgerSummaryRead, status_code=status.HTTP_201_CREATED)
async def register_ledger_customer(
    payload: LedgerCustomerRegisterPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:create"))],
) -> CustomerLedgerSummaryRead:
    return await ledger_svc.register_customer(db, payload.customer_id, current)


@router.post("/ledger/customers/{customer_id}/receivables", response_model=AccountingEntryRead, status_code=status.HTTP_201_CREATED)
async def create_ledger_receivable(
    customer_id: UUID,
    payload: LedgerReceivableCreatePayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:create"))],
) -> AccountingEntryRead:
    return await ledger_svc.create_manual_receivable(
        db,
        customer_id,
        payload,
        current,
        allow_backfill=_can_backfill(current),
    )


@router.get("/ledger/customers", response_model=PageResponse)
async def list_ledger_customers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    outstanding_only: bool = Query(default=False),
    q: str | None = Query(default=None, max_length=80),
) -> PageResponse:
    return await ledger_svc.list_customer_summaries(
        db, page=page, page_size=page_size, outstanding_only=outstanding_only, q=q
    )


@router.get("/ledger/customers/{customer_id}")
async def get_customer_ledger(
    customer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:read"))],
) -> dict:
    return await ledger_svc.get_customer_ledger_detail(db, customer_id)


@router.post("/ledger/receipts", response_model=AccountingEntryRead, status_code=status.HTTP_201_CREATED)
async def create_ledger_receipt(
    payload: ReceiptCreatePayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:confirm"))],
) -> AccountingEntryRead:
    return await ledger_svc.create_receipt_with_allocations(db, payload, current)


@router.post(
    "/procurement-payable-requests/from-entry/{entry_id}",
    response_model=ProcurementPayableRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_procurement_payable_request(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:post_payable"))],
) -> ProcurementPayableRequestRead:
    return await ppr_svc.create_request_from_entry(db, entry_id, current)


@router.get("/procurement-payable-requests/by-entry/{entry_id}", response_model=ProcurementPayableRequestRead | None)
async def get_procurement_payable_request_by_entry(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:read"))],
) -> ProcurementPayableRequestRead | None:
    return await ppr_svc.get_request_for_entry(db, entry_id)


@router.post("/procurement-payable-requests/{request_id}/approve", response_model=ProcurementPayableRequestRead)
async def approve_procurement_payable_request(
    request_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:approve_procurement_payable"))],
) -> ProcurementPayableRequestRead:
    return await ppr_svc.approve_request(db, request_id, current)


@router.post("/procurement-payable-requests/{request_id}/reject", response_model=ProcurementPayableRequestRead)
async def reject_procurement_payable_request(
    request_id: UUID,
    payload: ProcurementPayableRejectPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:accounting:approve_procurement_payable"))],
) -> ProcurementPayableRequestRead:
    return await ppr_svc.reject_request(db, request_id, current, reason=payload.reason)


@router.get("/entries/export")
async def export_accounting_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:accounting:read"))],
    customer_id: UUID | None = Query(default=None),
    supplier_id: UUID | None = Query(default=None),
    entry_kind: str | None = Query(default=None, max_length=32),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> StreamingResponse:
    await svc.require_accounting_enabled(db)
    from app.schemas.common import PageResponse
    result = await svc.list_entries(
        db,
        page=1,
        page_size=10000,
        customer_id=customer_id,
        supplier_id=supplier_id,
        entry_kind=entry_kind,
        include_void=False,
        date_from=date_from,
        date_to=date_to,
    )
    items: list[AccountingEntryRead] = result.items  # type: ignore[assignment]

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["单号", "类型", "客户", "供应商", "摘要", "金额", "已核销", "发生日", "到期日", "状态", "补录"])
    for e in items:
        writer.writerow([
            e.entry_no,
            e.entry_kind,
            e.customer_id,
            e.supplier_id,
            e.title,
            str(e.amount),
            str(e.settled_amount),
            str(e.occurred_on),
            str(e.due_date) if e.due_date else "",
            e.status,
            "是" if e.is_backfill else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=accounting_entries.csv"},
    )
