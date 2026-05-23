from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class QuoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    customer_id: UUID
    machine_id: UUID
    bom_id: UUID | None = None
    approval_template_id: UUID | None = None
    currency: str = Field(default="CNY", max_length=8)
    valid_until: date | None = None
    remark: str | None = None


class QuoteItemCreate(BaseModel):
    item_code: str = Field(min_length=1, max_length=64)
    item_name: str = Field(min_length=1, max_length=200)
    spec: str | None = Field(default=None, max_length=160)
    unit: str = Field(min_length=1, max_length=32)
    quantity: Decimal
    unit_price: Decimal
    source_type: str = Field(default="manual", max_length=32)
    remark: str | None = None


class QuoteVersionCreate(BaseModel):
    quote_id: UUID
    items: list[QuoteItemCreate] = Field(default_factory=list)


class QuoteItemRead(BaseModel):
    id: UUID
    quote_version_id: UUID
    item_code: str
    item_name: str
    spec: str | None = None
    unit: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    source_type: str
    remark: str | None = None

    model_config = {"from_attributes": True}


class QuoteApprovalRead(BaseModel):
    id: UUID
    quote_id: UUID
    approver_id: UUID | None = None
    action: str
    status: str
    comment: str | None = None
    acted_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalNodeRead(BaseModel):
    id: UUID
    template_id: UUID
    node_order: int
    node_name: str
    approver_role_code: str | None = None
    sign_mode: str
    min_amount: Decimal
    max_amount: Decimal | None = None

    model_config = {"from_attributes": True}


class QuoteRead(BaseModel):
    id: UUID
    quote_no: str
    title: str
    customer_id: UUID
    machine_id: UUID
    bom_id: UUID | None = None
    approval_template_id: UUID | None = None
    current_approval_order: int
    workflow_state: str
    currency: str
    total_amount: Decimal
    valid_until: date | None = None
    remark: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class QuoteVersionRead(BaseModel):
    id: UUID
    quote_id: UUID
    version_no: int
    bom_snapshot: dict | None = None
    cost_snapshot: dict | None = None
    analysis_snapshot: dict | None = None
    total_amount: Decimal
    total_cost: Decimal
    profit_amount: Decimal
    profit_rate: Decimal
    is_current: bool
    changed_at: datetime
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class QuoteDetailRead(QuoteRead):
    current_version: QuoteVersionRead | None = None
    items: list[QuoteItemRead] = Field(default_factory=list)


class QuoteActionPayload(BaseModel):
    action_code: str = Field(min_length=1, max_length=64)
    comment: str | None = None


class ApprovalTemplateCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    is_active: bool = True


class ApprovalNodeCreate(BaseModel):
    node_order: int = Field(ge=1)
    node_name: str = Field(min_length=1, max_length=120)
    approver_role_code: str | None = Field(default=None, max_length=64)
    sign_mode: str = Field(default="orsign", pattern="^(countersign|orsign)$")
    dynamic_approver_expr: str | None = Field(default=None, max_length=255)
    min_amount: Decimal = Decimal("0")
    max_amount: Decimal | None = None


class ApprovalTemplateWithNodesCreate(BaseModel):
    template: ApprovalTemplateCreate
    nodes: list[ApprovalNodeCreate] = Field(default_factory=list)


class ApprovalTemplateRead(BaseModel):
    id: UUID
    code: str
    name: str
    biz_type: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class ApprovalTemplateDetailRead(ApprovalTemplateRead):
    nodes: list[ApprovalNodeRead] = Field(default_factory=list)


class QuoteVersionDiffQuery(BaseModel):
    from_version_no: int = Field(ge=1)
    to_version_no: int = Field(ge=1)


class QuoteExportRequest(BaseModel):
    format: str = Field(pattern="^(pdf|xlsx)$")
    template_id: str | None = Field(default=None, max_length=64)


class QuoteWizardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    customer_id: UUID
    machine_id: UUID
    bom_id: UUID | None = None
    approval_template_id: UUID | None = None
    currency: str = Field(default="CNY", max_length=8)
    valid_until: date | None = None
    remark: str | None = None
    initial_items: list[QuoteItemCreate] = Field(default_factory=list)


class QuoteExportTaskRead(BaseModel):
    id: UUID
    quote_id: UUID
    format: str
    status: str
    file_id: UUID | None = None
    error_message: str | None = None
    requested_at: datetime
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}
