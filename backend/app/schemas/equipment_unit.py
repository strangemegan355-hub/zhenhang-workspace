from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EquipmentUnitCreate(BaseModel):
    serial_number: str = Field(max_length=80)
    machine_id: UUID
    build_status: str = Field(default="in_production", max_length=32)
    project_id: UUID | None = None
    customer_id: UUID | None = None
    build_start_date: date | None = None
    ship_date: date | None = None
    install_date: date | None = None
    acceptance_date: date | None = None
    warranty_expiry_date: date | None = None
    remarks: str | None = None


class EquipmentUnitUpdate(BaseModel):
    serial_number: str | None = Field(default=None, max_length=80)
    machine_id: UUID | None = None
    build_status: str | None = Field(default=None, max_length=32)
    project_id: UUID | None = None
    customer_id: UUID | None = None
    build_start_date: date | None = None
    ship_date: date | None = None
    install_date: date | None = None
    acceptance_date: date | None = None
    warranty_expiry_date: date | None = None
    remarks: str | None = None


class EquipmentUnitRead(BaseModel):
    id: UUID
    serial_number: str
    machine_id: UUID
    build_status: str
    project_id: UUID | None = None
    customer_id: UUID | None = None
    build_start_date: date | None = None
    ship_date: date | None = None
    install_date: date | None = None
    acceptance_date: date | None = None
    warranty_expiry_date: date | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
