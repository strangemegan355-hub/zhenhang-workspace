from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: UUID
    channel: str
    title: str
    content: str
    biz_type: str
    biz_id: UUID | None = None
    receiver_id: UUID | None = None
    status: str
    sent_at: datetime | None = None
    read_at: datetime | None = None
    payload: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationUnreadCount(BaseModel):
    unread: int
