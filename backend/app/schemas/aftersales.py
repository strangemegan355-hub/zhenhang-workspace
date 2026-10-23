from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AfterSalesServiceRequestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    customer_id: UUID
    equipment_unit_id: UUID | None = None
    priority: str = Field(default="medium")
    description: str | None = Field(default=None, max_length=2000)
    assigned_to: UUID | None = None
    scheduled_date: date | None = None


class AfterSalesServiceRequestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    priority: str | None = None
    status: str | None = None
    description: str | None = Field(default=None, max_length=2000)
    assigned_to: UUID | None = None
    scheduled_date: date | None = None
    resolution: str | None = Field(default=None, max_length=2000)


class AfterSalesServiceRequestRead(BaseModel):
    id: UUID
    request_no: str
    title: str
    customer_id: UUID
    customer_name: str | None = None
    equipment_unit_id: UUID | None = None
    equipment_serial: str | None = None
    status: str
    priority: str
    description: str | None = None
    assigned_to: UUID | None = None
    assignee_name: str | None = None
    scheduled_date: date | None = None
    completed_date: date | None = None
    resolution: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None

    model_config = {"from_attributes": True}
