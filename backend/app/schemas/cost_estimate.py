from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CostEstimateMaterialLineInput(BaseModel):
    material_id: UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    spec: str | None = Field(default=None, max_length=200)
    qty: Decimal = Field(default=Decimal("1"), gt=0)
    unit: str = Field(default="EA", max_length=32)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    sort_order: int = 0


class CostEstimateMachineLineInput(BaseModel):
    machine_id: UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    spec: str | None = Field(default=None, max_length=200)
    power_kw: str | None = Field(default=None, max_length=64)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    qty: Decimal = Field(default=Decimal("1"), gt=0)
    sort_order: int = 0


class CostEstimateProcessLineInput(BaseModel):
    process_name: str = Field(min_length=1, max_length=120)
    equipment: str | None = Field(default=None, max_length=120)
    hours: Decimal = Field(default=Decimal("0"), ge=0)
    rate: Decimal = Field(default=Decimal("0"), ge=0)
    sort_order: int = 0


class CostEstimateMaterialLineRead(CostEstimateMaterialLineInput):
    id: UUID
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CostEstimateMachineLineRead(CostEstimateMachineLineInput):
    id: UUID
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CostEstimateProcessLineRead(CostEstimateProcessLineInput):
    id: UUID
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CostEstimateSummary(BaseModel):
    material_cost: Decimal
    machine_cost: Decimal
    labor_cost: Decimal
    other_cost: Decimal
    base_cost: Decimal
    scrap_cost: Decimal
    overhead_cost: Decimal
    total_cost: Decimal
    profit_amount: Decimal
    before_tax: Decimal
    tax_amount: Decimal
    final_total: Decimal
    unit_final: Decimal


class CostEstimateBase(BaseModel):
    product_name: str = Field(min_length=1, max_length=160)
    product_spec: str | None = Field(default=None, max_length=200)
    power_kw: str | None = Field(default=None, max_length=64)
    customer_id: UUID | None = None
    project_id: UUID | None = None
    drawing_no: str | None = Field(default=None, max_length=120)
    qty: Decimal = Field(default=Decimal("1"), gt=0)
    delivery_note: str | None = Field(default=None, max_length=255)
    remark: str | None = None
    outsource_cost: Decimal = Field(default=Decimal("0"), ge=0)
    logistics_cost: Decimal = Field(default=Decimal("0"), ge=0)
    scrap_rate: float | None = Field(default=None, ge=0, le=100)
    overhead_rate: float | None = Field(default=None, ge=0, le=100)
    profit_rate: float | None = Field(default=None, ge=0, le=100)
    tax_rate: float | None = Field(default=None, ge=0, le=100)


class CostEstimateCreate(CostEstimateBase):
    material_lines: list[CostEstimateMaterialLineInput] = Field(default_factory=list)
    machine_lines: list[CostEstimateMachineLineInput] = Field(default_factory=list)
    process_lines: list[CostEstimateProcessLineInput] = Field(default_factory=list)


class CostEstimateUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=160)
    product_spec: str | None = Field(default=None, max_length=200)
    power_kw: str | None = Field(default=None, max_length=64)
    customer_id: UUID | None = None
    project_id: UUID | None = None
    drawing_no: str | None = Field(default=None, max_length=120)
    qty: Decimal | None = Field(default=None, gt=0)
    delivery_note: str | None = Field(default=None, max_length=255)
    remark: str | None = None
    status: str | None = Field(default=None, max_length=32)
    outsource_cost: Decimal | None = Field(default=None, ge=0)
    logistics_cost: Decimal | None = Field(default=None, ge=0)
    scrap_rate: float | None = Field(default=None, ge=0, le=100)
    overhead_rate: float | None = Field(default=None, ge=0, le=100)
    profit_rate: float | None = Field(default=None, ge=0, le=100)
    tax_rate: float | None = Field(default=None, ge=0, le=100)
    material_lines: list[CostEstimateMaterialLineInput] | None = None
    machine_lines: list[CostEstimateMachineLineInput] | None = None
    process_lines: list[CostEstimateProcessLineInput] | None = None


class CostEstimateRead(CostEstimateBase):
    id: UUID
    estimate_no: str
    status: str
    scrap_rate: Decimal
    overhead_rate: Decimal
    profit_rate: Decimal
    tax_rate: Decimal
    material_cost: Decimal
    machine_cost: Decimal
    labor_cost: Decimal
    other_cost: Decimal
    base_cost: Decimal
    scrap_cost: Decimal
    overhead_cost: Decimal
    total_cost: Decimal
    profit_amount: Decimal
    before_tax: Decimal
    tax_amount: Decimal
    final_total: Decimal
    unit_final: Decimal
    material_lines: list[CostEstimateMaterialLineRead] = Field(default_factory=list)
    machine_lines: list[CostEstimateMachineLineRead] = Field(default_factory=list)
    process_lines: list[CostEstimateProcessLineRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class CostEstimateListItem(BaseModel):
    id: UUID
    estimate_no: str
    product_name: str
    customer_id: UUID | None = None
    qty: Decimal
    status: str
    total_cost: Decimal
    final_total: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


class CostEstimatePreviewRequest(CostEstimateCreate):
    pass


class CostEstimatePreviewResponse(CostEstimateSummary):
    pass
