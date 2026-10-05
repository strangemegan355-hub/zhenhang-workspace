from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UnitBase(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=80)
    status: str = Field(default="active", max_length=32)
    remark: str | None = None


class UnitCreate(UnitBase):
    pass


class UnitUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=32)
    name: str | None = Field(default=None, min_length=1, max_length=80)
    status: str | None = Field(default=None, max_length=32)
    remark: str | None = None


class UnitRead(UnitBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}
