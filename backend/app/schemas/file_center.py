from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FileObjectRead(BaseModel):
    id: UUID
    bucket: str
    object_name: str
    file_name: str
    file_ext: str | None = None
    mime_type: str | None = None
    size_bytes: int
    category: str
    preview_url: str | None = None
    checksum: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class FileRelationCreate(BaseModel):
    file_id: UUID
    biz_type: str = Field(min_length=1, max_length=64)
    biz_id: UUID
    relation_type: str = Field(default="attachment", max_length=32)
    remark: str | None = None


class FileRelationRead(BaseModel):
    id: UUID
    file_id: UUID
    biz_type: str
    biz_id: UUID
    relation_type: str
    remark: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}
