from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InstallStepItem(BaseModel):
    step: str = Field(default="")
    description: str = Field(default="")
    completed: bool = False
    completed_at: datetime | None = None
    remark: str = Field(default="")


class CommissioningItem(BaseModel):
    category: str = Field(default="")
    check_point: str = Field(default="")
    expected: str = Field(default="")
    actual_result: str = Field(default="")
    pass_: bool = Field(default=True, alias="pass")
    remark: str = Field(default="")


# ── Create / Update ──

class InstallationPlanCreate(BaseModel):
    equipment_unit_id: UUID
    planned_start_date: datetime | None = None
    planned_end_date: datetime | None = None
    install_items: list[InstallStepItem] = Field(default_factory=list)
    commissioning_items: list[CommissioningItem] = Field(default_factory=list)
    remarks: str | None = None


class InstallationPlanUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=16)
    planned_start_date: datetime | None = None
    planned_end_date: datetime | None = None
    actual_start_date: datetime | None = None
    actual_end_date: datetime | None = None
    install_items: list[InstallStepItem] | None = None
    commissioning_items: list[CommissioningItem] | None = None
    customer_representative: str | None = None
    customer_accepted: bool | None = None


# ── Read ──

class InstallationPlanRead(BaseModel):
    id: UUID
    equipment_unit_id: UUID
    planned_start_date: datetime | None = None
    planned_end_date: datetime | None = None
    actual_start_date: datetime | None = None
    actual_end_date: datetime | None = None
    status: str
    install_items: list | None = None
    commissioning_items: list | None = None
    customer_representative: str | None = None
    customer_accepted: bool
    customer_accepted_date: datetime | None = None
    remarks: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
