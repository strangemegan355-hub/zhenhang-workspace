from datetime import datetime
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class MachineCategoryBase(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    parent_id: UUID | None = None
    description: str | None = None


class MachineCategoryCreate(MachineCategoryBase):
    pass


class MachineCategoryUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    parent_id: UUID | None = None
    description: str | None = None


class MachineCategoryRead(MachineCategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class MachineBase(BaseModel):
    category_id: UUID | None = None
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    model_no: str | None = Field(default=None, max_length=120)
    status: str = Field(default="draft", max_length=32)
    description: str | None = None


class MachineCreate(MachineBase):
    model_config = {
        "json_schema_extra": {
            "example": {
                "category_id": None,
                "code": "INJ-280T",
                "name": "280T 注塑机",
                "model_no": "ZH-280A",
                "status": "draft",
                "description": "标准机型",
            }
        }
    }


class MachineUpdate(BaseModel):
    category_id: UUID | None = None
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    model_no: str | None = Field(default=None, max_length=120)
    status: str | None = Field(default=None, max_length=32)
    description: str | None = None


class MachineRead(MachineBase):
    id: UUID
    machine_code: str
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class MachineParameterBase(BaseModel):
    machine_id: UUID
    param_key: str = Field(min_length=1, max_length=64)
    param_name: str = Field(min_length=1, max_length=120)
    value: str | None = Field(default=None, max_length=255)
    unit: str | None = Field(default=None, max_length=32)
    sort_order: int = 0
    remarks: str | None = None


class MachineParameterCreate(MachineParameterBase):
    pass


class MachineParameterUpdate(BaseModel):
    param_key: str | None = Field(default=None, min_length=1, max_length=64)
    param_name: str | None = Field(default=None, min_length=1, max_length=120)
    value: str | None = Field(default=None, max_length=255)
    unit: str | None = Field(default=None, max_length=32)
    sort_order: int | None = None
    remarks: str | None = None


class MachineParameterRead(MachineParameterBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class MachineImageBase(BaseModel):
    machine_id: UUID
    file_url: str = Field(min_length=1, max_length=500)
    file_name: str | None = Field(default=None, max_length=200)
    sort_order: int = 0


class MachineImageCreate(MachineImageBase):
    pass


class MachineImageUpdate(BaseModel):
    file_url: str | None = Field(default=None, min_length=1, max_length=500)
    file_name: str | None = Field(default=None, max_length=200)
    sort_order: int | None = None


class MachineImageRead(MachineImageBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class MachineBomBase(BaseModel):
    machine_id: UUID
    version: str = Field(min_length=1, max_length=64)
    is_active: bool = False
    effective_date: date | None = None
    total_cost: Decimal = Decimal("0")
    status: str = Field(default="draft", max_length=32)
    remark: str | None = None


class MachineBomCreate(MachineBomBase):
    model_config = {
        "json_schema_extra": {
            "example": {
                "machine_id": "11111111-1111-1111-1111-111111111111",
                "version": "V1.0",
                "is_active": False,
                "effective_date": "2026-06-01",
                "status": "draft",
                "remark": "首版BOM",
            }
        }
    }


class MachineBomUpdate(BaseModel):
    version: str | None = Field(default=None, min_length=1, max_length=64)
    is_active: bool | None = None
    effective_date: date | None = None
    status: str | None = Field(default=None, max_length=32)
    remark: str | None = None


class MachineBomRead(MachineBomBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class MachineBomItemBase(BaseModel):
    bom_id: UUID
    item_code: str = Field(min_length=1, max_length=64)
    item_name: str = Field(min_length=1, max_length=160)
    spec: str | None = Field(default=None, max_length=160)
    unit: str = Field(min_length=1, max_length=32)
    quantity: Decimal
    unit_cost: Decimal = Decimal("0")
    line_total: Decimal = Decimal("0")
    loss_rate: Decimal = Decimal("0")
    sort_order: int = 0
    remark: str | None = None


class MachineBomItemCreate(MachineBomItemBase):
    model_config = {
        "json_schema_extra": {
            "example": {
                "bom_id": "11111111-1111-1111-1111-111111111111",
                "item_code": "SCREW-M30",
                "item_name": "螺杆总成",
                "spec": "M30",
                "unit": "set",
                "quantity": 1,
                "unit_cost": 4200.5,
                "loss_rate": 0.01,
                "sort_order": 1,
                "remark": "核心零件",
            }
        }
    }


class MachineBomItemUpdate(BaseModel):
    item_code: str | None = Field(default=None, min_length=1, max_length=64)
    item_name: str | None = Field(default=None, min_length=1, max_length=160)
    spec: str | None = Field(default=None, max_length=160)
    unit: str | None = Field(default=None, min_length=1, max_length=32)
    quantity: Decimal | None = None
    unit_cost: Decimal | None = None
    line_total: Decimal | None = None
    loss_rate: Decimal | None = None
    sort_order: int | None = None
    remark: str | None = None


class MachineBomItemRead(MachineBomItemBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class BatchMachineBomItemCreate(BaseModel):
    items: list[MachineBomItemCreate]

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "bom_id": "11111111-1111-1111-1111-111111111111",
                        "item_code": "SCREW-M30",
                        "item_name": "螺杆总成",
                        "spec": "M30",
                        "unit": "set",
                        "quantity": 1,
                        "unit_cost": 4200.5,
                        "loss_rate": 0.01,
                        "sort_order": 1,
                    },
                    {
                        "bom_id": "11111111-1111-1111-1111-111111111111",
                        "item_code": "BARREL-280",
                        "item_name": "料筒",
                        "spec": "280",
                        "unit": "pcs",
                        "quantity": 1,
                        "unit_cost": 3800,
                        "loss_rate": 0.02,
                        "sort_order": 2,
                    },
                ]
            }
        }
    }


class BatchIdsPayload(BaseModel):
    ids: list[UUID] = Field(min_length=1)
