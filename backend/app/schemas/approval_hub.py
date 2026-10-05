from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ApprovalTaskRead(BaseModel):
    id: str
    task_type: str
    title: str
    subtitle: str | None = None
    amount: Decimal | None = None
    discount_amount: Decimal | None = None
    discount_rate_pct: Decimal | None = None
    submitter_name: str | None = None
    submitted_at: datetime
    status: str = "pending"
    source_id: UUID | None = None
    source_no: str | None = None
    detail_href: str | None = None
    can_approve: bool = True


class ApprovalInboxResponse(BaseModel):
    total: int
    items: list[ApprovalTaskRead]


class ApprovalActionPayload(BaseModel):
    task_type: str = Field(min_length=1, max_length=64)
    task_id: UUID
    action: str = Field(pattern="^(approve|reject)$")
    comment: str | None = Field(default=None, max_length=500)
