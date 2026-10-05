from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProcurementEntryCreate(BaseModel):
    request_no: str | None = Field(default=None, max_length=64)
    project_id: UUID | None = None
    material_id: UUID
    supplier_id: UUID
    qty: Decimal = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    lead_days: int = Field(default=7, ge=0)
    need_date: date | None = None
    status: str = Field(default="planned", max_length=32)
    remark: str | None = None


class ProcurementEntryUpdate(BaseModel):
    project_id: UUID | None = None
    material_id: UUID | None = None
    supplier_id: UUID | None = None
    qty: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, gt=0)
    lead_days: int | None = Field(default=None, ge=0)
    need_date: date | None = None
    status: str | None = Field(default=None, max_length=32)
    remark: str | None = None


class ProcurementEntryRead(BaseModel):
    id: UUID
    request_no: str
    project_id: UUID | None
    material_id: UUID
    supplier_id: UUID
    qty: Decimal
    unit_price: Decimal
    plan_amount: Decimal
    lead_days: int
    need_date: date | None
    status: str
    transferred_to_actual: bool
    payable_status: str = "none"
    remark: str | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class ProcurementTransferResult(BaseModel):
    transferred_count: int
    skipped_count: int
    items: list[dict]
