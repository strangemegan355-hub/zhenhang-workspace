from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AccountingFeatureFlags(BaseModel):
    accounting_enabled: bool = False
    quote_receivable_enabled: bool = False
    procurement_approval_enabled: bool = False


ENTRY_KINDS = ("receivable", "payable", "receipt", "payment", "revenue", "expense")
CUSTOMER_KINDS = {"receivable", "receipt", "revenue"}
SUPPLIER_KINDS = {"payable", "payment", "expense"}


class AccountingEntryCreate(BaseModel):
    entry_kind: str = Field(min_length=1, max_length=32)
    customer_id: UUID | None = None
    supplier_id: UUID | None = None
    project_id: UUID | None = None
    amount: Decimal = Field(gt=0)
    occurred_on: date
    due_date: date | None = None
    title: str = Field(min_length=1, max_length=200)
    remark: str | None = Field(default=None, max_length=500)
    is_backfill: bool = False

    @field_validator("entry_kind")
    @classmethod
    def validate_kind(cls, value: str) -> str:
        if value not in ENTRY_KINDS:
            raise ValueError(f"entry_kind must be one of: {', '.join(ENTRY_KINDS)}")
        return value


class AccountingEntryUpdate(BaseModel):
    customer_id: UUID | None = None
    supplier_id: UUID | None = None
    project_id: UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    occurred_on: date | None = None
    due_date: date | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    remark: str | None = Field(default=None, max_length=500)


class AccountingEntryLineRead(BaseModel):
    id: UUID
    product_id: UUID | None = None
    item_name: str
    spec: str | None = None
    unit: str | None = None
    qty: Decimal
    unit_price: Decimal
    line_amount: Decimal
    sort_order: int = 0

    model_config = {"from_attributes": True}


class AccountingEntryRead(BaseModel):
    id: UUID
    entry_no: str
    entry_kind: str
    status: str
    party_type: str | None = None
    customer_id: UUID | None = None
    supplier_id: UUID | None = None
    project_id: UUID | None = None
    quote_id: UUID | None = None
    amount: Decimal
    settled_amount: Decimal
    currency: str
    occurred_on: date
    due_date: date | None = None
    booked_on: date
    is_backfill: bool
    source_type: str
    source_id: UUID | None = None
    source_no: str | None = None
    approval_status: str
    title: str
    remark: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    lines: list[AccountingEntryLineRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class AccountingModuleStatus(BaseModel):
    module: str = "accounting"
    schema_version: str = "0029"
    flags: AccountingFeatureFlags
    entry_count: int = 0


class QuoteReceivableRequestRead(BaseModel):
    id: UUID
    quote_id: UUID
    requested_by: UUID
    requested_amount: Decimal
    standard_amount: Decimal
    discount_amount: Decimal
    discount_rate_pct: Decimal
    needs_boss_approval: bool
    approval_status: str
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    reject_reason: str | None = None
    receivable_entry_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuoteReceivableRejectPayload(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class ProcurementPayableRequestRead(BaseModel):
    id: UUID
    procurement_entry_id: UUID
    requested_by: UUID
    requested_amount: Decimal
    approval_status: str
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    reject_reason: str | None = None
    payable_entry_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProcurementPayableRejectPayload(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


SOURCE_TYPE_LABELS = {
    "manual": "手录账目",
    "customer_quote": "对客报价",
    "fieldwork_repair": "外出维修",
    "fieldwork_loading": "装车登记",
    "procurement": "采购",
}


class ReceiptAllocationItem(BaseModel):
    receivable_entry_id: UUID
    amount: Decimal = Field(gt=0)


class ReceiptCreatePayload(BaseModel):
    customer_id: UUID
    amount: Decimal = Field(gt=0)
    occurred_on: date
    title: str = Field(min_length=1, max_length=200)
    remark: str | None = Field(default=None, max_length=500)
    allocations: list[ReceiptAllocationItem] = Field(min_length=1)


class CustomerLedgerSummaryRead(BaseModel):
    customer_id: UUID
    customer_name: str
    customer_code: str | None = None
    receivable_total: Decimal
    received_total: Decimal
    outstanding_total: Decimal
    open_bill_count: int
    last_occurred_on: date | None = None
    is_registered: bool = False


class LedgerCustomerRegisterPayload(BaseModel):
    customer_id: UUID


class LedgerReceivableCreatePayload(BaseModel):
    amount: Decimal = Field(gt=0)
    occurred_on: date
    title: str = Field(min_length=1, max_length=200)
    remark: str | None = Field(default=None, max_length=500)
    is_backfill: bool = False


class LedgerEntryRead(BaseModel):
    id: UUID
    entry_no: str
    entry_kind: str
    status: str
    customer_id: UUID | None = None
    amount: Decimal
    settled_amount: Decimal
    open_amount: Decimal
    payment_status: str | None = None
    source_type: str
    source_label: str
    source_no: str | None = None
    quote_id: UUID | None = None
    occurred_on: date
    title: str
    remark: str | None = None
    is_backfill: bool
    allocations: list[dict] = Field(default_factory=list)


# ── Supplier ledger ──


class SupplierLedgerSummaryRead(BaseModel):
    supplier_id: UUID
    supplier_name: str
    supplier_code: str | None = None
    payable_total: Decimal
    paid_total: Decimal
    outstanding_total: Decimal
    open_bill_count: int
    last_occurred_on: date | None = None
    is_registered: bool = False


class LedgerSupplierRegisterPayload(BaseModel):
    supplier_id: UUID


class LedgerPayableCreatePayload(BaseModel):
    amount: Decimal = Field(gt=0)
    occurred_on: date
    due_date: date | None = None
    title: str = Field(min_length=1, max_length=200)
    remark: str | None = Field(default=None, max_length=500)
    is_backfill: bool = False


class SupplierLedgerDetailRead(BaseModel):
    supplier_id: UUID
    supplier_name: str
    supplier_code: str | None = None
    is_registered: bool
    payable_total: Decimal
    paid_total: Decimal
    outstanding_total: Decimal
    entries: list[LedgerEntryRead] = Field(default_factory=list)


class PaymentAllocationItem(BaseModel):
    payable_entry_id: UUID
    amount: Decimal = Field(gt=0)


class PaymentCreatePayload(BaseModel):
    supplier_id: UUID
    amount: Decimal = Field(gt=0)
    occurred_on: date
    title: str = Field(min_length=1, max_length=200)
    remark: str | None = Field(default=None, max_length=500)
    allocations: list[PaymentAllocationItem] = Field(min_length=1)
