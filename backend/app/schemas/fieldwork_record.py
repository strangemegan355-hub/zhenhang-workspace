from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class FieldworkRecordCreate(BaseModel):
    record_type: str = Field(max_length=32)
    customer_id: UUID | None = None
    project_id: UUID | None = None
    machine_id: UUID | None = None
    material_id: UUID | None = None
    occurred_on: date | None = None
    reporter_name: str | None = Field(default=None, max_length=120)
    headline: str = Field(min_length=1, max_length=255)
    detail: str | None = None
    qty: Decimal | None = Field(default=None, gt=0)
    hours: Decimal | None = Field(default=None, ge=0)
    repair_amount: Decimal | None = Field(default=None, gt=0)
    urgency: str | None = Field(default=None, max_length=32)
    extra: dict | None = None
    remark: str | None = None
    service_request_id: UUID | None = None


class FieldworkRecordUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=32)
    detail: str | None = None
    urgency: str | None = Field(default=None, max_length=32)
    remark: str | None = None
    repair_amount: Decimal | None = Field(default=None, gt=0)


class FieldworkRecordRead(BaseModel):
    id: UUID
    record_no: str
    record_type: str
    record_type_label: str
    status: str
    status_label: str
    customer_id: UUID | None
    project_id: UUID | None
    machine_id: UUID | None
    material_id: UUID | None
    occurred_on: date | None
    reporter_name: str | None
    headline: str
    detail: str | None
    qty: Decimal | None
    hours: Decimal | None
    repair_amount: Decimal | None
    receivable_entry_id: UUID | None
    service_request_id: UUID | None = None
    service_request_title: str | None = None
    urgency: str | None
    urgency_label: str | None
    extra: dict | None
    remark: str | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class FieldworkSummary(BaseModel):
    total: int
    repair: int
    shortage: int
    loading: int
    open_shortages: int
