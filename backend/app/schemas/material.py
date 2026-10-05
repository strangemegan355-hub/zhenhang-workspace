from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class MaterialBase(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    spec: str | None = Field(default=None, max_length=200)
    unit: str = Field(default="EA", max_length=32)
    reference_price: Decimal = Field(default=Decimal("0"), ge=0)
    category_id: UUID | None = None
    category: str | None = Field(default=None, max_length=80)
    status: str = Field(default="active", max_length=32)
    remark: str | None = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    spec: str | None = Field(default=None, max_length=200)
    unit: str | None = Field(default=None, max_length=32)
    reference_price: Decimal | None = Field(default=None, ge=0)
    category_id: UUID | None = None
    category: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, max_length=32)
    remark: str | None = None


class MaterialRead(MaterialBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}
