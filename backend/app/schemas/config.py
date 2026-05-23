from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SystemConfigCreate(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: str
    value_type: str = Field(default="string", max_length=32)
    group: str = Field(default="default", max_length=64)
    description: str | None = None
    is_public: bool = False


class SystemConfigUpdate(BaseModel):
    value: str | None = None
    value_type: str | None = Field(default=None, max_length=32)
    group: str | None = Field(default=None, max_length=64)
    description: str | None = None
    is_public: bool | None = None


class SystemConfigRead(BaseModel):
    id: UUID
    key: str
    value: str
    value_type: str
    group: str
    description: str | None = None
    is_public: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}
