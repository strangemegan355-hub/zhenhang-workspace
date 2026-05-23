from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogRead(BaseModel):
    id: UUID
    module: str
    action: str
    resource_type: str
    resource_id: UUID | None = None
    detail: str | None = None
    payload: dict | None = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class AuditLogQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    q: str | None = Field(default=None, max_length=120)
    module: str | None = Field(default=None, max_length=64)
    action: str | None = Field(default=None, max_length=64)
    resource_type: str | None = Field(default=None, max_length=64)
