from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    customer_id: UUID | None = None
    category: str | None = Field(default=None, max_length=80)
    stage: str = Field(default="lead", max_length=32)
    owner_name: str | None = Field(default=None, max_length=120)
    primary_quote_id: UUID | None = None
    target_date: date | None = None
    remark: str | None = None
    status: str = Field(default="active", max_length=32)


class ProjectCreate(ProjectBase):
    project_no: str | None = Field(default=None, max_length=64)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    customer_id: UUID | None = None
    category: str | None = Field(default=None, max_length=80)
    stage: str | None = Field(default=None, max_length=32)
    owner_name: str | None = Field(default=None, max_length=120)
    primary_quote_id: UUID | None = None
    target_date: date | None = None
    remark: str | None = None
    status: str | None = Field(default=None, max_length=32)


class ProjectRead(ProjectBase):
    id: UUID
    project_no: str
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class ProjectLinkedQuote(BaseModel):
    id: UUID
    quote_no: str
    title: str
    quote_kind: str
    total_amount: Decimal
    workflow_state: str


class ProjectLinkedCostEstimate(BaseModel):
    id: UUID
    estimate_no: str
    product_name: str
    total_cost: Decimal
    final_total: Decimal


class ProjectProfitSnapshot(BaseModel):
    revenue_before_tax: Decimal | None = None
    revenue_tax_inclusive: Decimal | None = None
    budget_cost: Decimal | None = None
    expected_profit: Decimal | None = None
    profit_margin_pct: Decimal | None = None
    actual_cost_total: Decimal | None = None
    cost_variance: Decimal | None = None
    realized_profit: Decimal | None = None
    realized_margin_pct: Decimal | None = None
    link_status: str
    health: str
    budget_status: str


class ProjectProfitLedgerItem(BaseModel):
    id: UUID
    project_no: str
    name: str
    stage: str
    owner_name: str | None = None
    profit_snapshot: ProjectProfitSnapshot


class ProjectProfitLedgerTotals(BaseModel):
    budget_cost_total: Decimal | None = None
    actual_cost_total: Decimal | None = None
    variance_total: Decimal | None = None
    realized_profit_total: Decimal | None = None
    over_budget_count: int = 0


class ProjectProfitLedgerResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProjectProfitLedgerItem]
    totals: ProjectProfitLedgerTotals


class ProjectSummaryRead(ProjectRead):
    linked_quote: ProjectLinkedQuote | None = None
    linked_cost_estimate: ProjectLinkedCostEstimate | None = None
    quote_count: int = 0
    cost_estimate_count: int = 0
    actual_cost_count: int = 0
    profit_snapshot: ProjectProfitSnapshot | None = None
