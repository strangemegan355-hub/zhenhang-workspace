from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WorkOrderCreate(BaseModel):
    work_order_no: str | None = Field(default=None, max_length=64)
    project_id: UUID
    machine_id: UUID | None = None
    task_desc: str = Field(min_length=1, max_length=255)
    process_node: str = Field(default="assembly", max_length=32)
    team: str | None = Field(default=None, max_length=120)
    owner_name: str | None = Field(default=None, max_length=120)
    plan_start: date | None = None
    plan_end: date | None = None
    drawing_version: str | None = Field(default=None, max_length=32)
    exception_type: str | None = Field(default=None, max_length=32)
    remark: str | None = None


class WorkOrderUpdate(BaseModel):
    machine_id: UUID | None = None
    task_desc: str | None = Field(default=None, min_length=1, max_length=255)
    process_node: str | None = Field(default=None, max_length=32)
    team: str | None = Field(default=None, max_length=120)
    owner_name: str | None = Field(default=None, max_length=120)
    plan_start: date | None = None
    plan_end: date | None = None
    drawing_version: str | None = Field(default=None, max_length=32)
    exception_type: str | None = Field(default=None, max_length=32)
    remark: str | None = None


class WorkOrderClaim(BaseModel):
    claimed_by: str = Field(min_length=1, max_length=120)


class WorkOrderGenerateChain(BaseModel):
    project_id: UUID
    start_date: date | None = None
    step_days: int = Field(default=3, ge=1, le=30)
    drawing_version: str = Field(default="V1", max_length=32)


class WorkOrderRead(BaseModel):
    id: UUID
    work_order_no: str
    project_id: UUID
    machine_id: UUID | None
    task_desc: str
    process_node: str
    process_node_label: str
    team: str | None
    owner_name: str | None
    claimed_by: str | None
    status: str
    status_label: str
    plan_start: date | None
    plan_end: date | None
    actual_start: datetime | None
    actual_end: datetime | None
    actual_hours: float
    drawing_version: str | None
    exception_type: str | None
    remark: str | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class WorkOrderSummary(BaseModel):
    total: int
    todo: int
    doing: int
    done: int
    exception_count: int
    completed_today: int


class WorkOrderChainResult(BaseModel):
    created_count: int
    items: list[WorkOrderRead]
