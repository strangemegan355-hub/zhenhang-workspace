from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Template items ──

class TemplateItem(BaseModel):
    category: str = Field(default="")
    check_point: str = Field(default="")
    standard: str = Field(default="")
    method: str = Field(default="")


# ── Record items (with results) ──

class RecordItem(BaseModel):
    category: str = Field(default="")
    check_point: str = Field(default="")
    standard: str = Field(default="")
    actual_result: str = Field(default="")
    pass_: bool = Field(default=True, alias="pass")
    remark: str = Field(default="")


# ── Template schemas ──

class AcceptanceTemplateCreate(BaseModel):
    name: str = Field(max_length=200)
    template_type: str = Field(max_length=8, default="fat")
    machine_id: UUID | None = None
    items: list[TemplateItem] = Field(default_factory=list)


class AcceptanceTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    machine_id: UUID | None = None
    items: list[TemplateItem] | None = None


class AcceptanceTemplateRead(BaseModel):
    id: UUID
    name: str
    template_type: str
    machine_id: UUID | None = None
    items: list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Record schemas ──

class AcceptanceRecordCreate(BaseModel):
    template_id: UUID
    test_date: datetime
    inspector_name: str = Field(max_length=120)
    items: list[RecordItem] = Field(default_factory=list)
    remarks: str | None = None


class AcceptanceRecordUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=16)
    items: list[RecordItem] | None = None
    overall_result: str | None = None
    remarks: str | None = None


class AcceptanceRecordRead(BaseModel):
    id: UUID
    template_id: UUID
    equipment_unit_id: UUID
    record_no: str
    test_date: datetime
    inspector_name: str
    status: str
    items: list | None = None
    overall_result: str | None = None
    remarks: str | None = None
    created_at: datetime
    punch_items: list | None = None

    model_config = {"from_attributes": True}


# ── Punch list schemas ──

class PunchListItemCreate(BaseModel):
    description: str
    severity: str = Field(default="minor", max_length=12)


class PunchListItemUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=12)
    resolution: str | None = None


class PunchListItemRead(BaseModel):
    id: UUID
    record_id: UUID
    description: str
    severity: str
    status: str
    resolved_at: datetime | None = None
    resolution: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
