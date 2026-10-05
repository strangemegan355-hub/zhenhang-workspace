from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectActualCostCreate(BaseModel):
    project_id: UUID
    cost_category: str = Field(min_length=1, max_length=32)
    cost_item_code: str | None = Field(default=None, max_length=32)
    cost_item_name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0)
    source: str = Field(default="采购", min_length=1, max_length=64)
    supplier_id: UUID | None = None
    occurred_on: date
    remark: str | None = None
    procurement_ref: str | None = Field(default=None, max_length=64)


class ProjectActualCostRead(BaseModel):
    id: UUID
    project_id: UUID
    cost_category: str
    cost_item_code: str | None
    cost_item_name: str
    amount: Decimal
    source: str
    supplier_id: UUID | None
    occurred_on: date
    remark: str | None
    procurement_ref: str | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}
