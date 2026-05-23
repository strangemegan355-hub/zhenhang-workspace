from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class CustomerBase(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    short_name: str | None = Field(default=None, max_length=80)
    industry: str | None = Field(default=None, max_length=80)
    level: str | None = Field(default=None, max_length=32)
    status: str = Field(default="active", max_length=32)
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=255)
    remarks: str | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    short_name: str | None = Field(default=None, max_length=80)
    industry: str | None = Field(default=None, max_length=80)
    level: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=32)
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=255)
    remarks: str | None = None


class CustomerRead(CustomerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class CustomerContactBase(BaseModel):
    customer_id: UUID
    name: str = Field(min_length=1, max_length=80)
    position: str | None = Field(default=None, max_length=80)
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    wechat: str | None = Field(default=None, max_length=80)
    remarks: str | None = None


class CustomerContactCreate(CustomerContactBase):
    pass


class CustomerContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    position: str | None = Field(default=None, max_length=80)
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    wechat: str | None = Field(default=None, max_length=80)
    remarks: str | None = None


class CustomerContactRead(CustomerContactBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class CustomerFollowupBase(BaseModel):
    customer_id: UUID
    contact_id: UUID | None = None
    followup_type: str = Field(default="phone", max_length=32)
    content: str
    followup_at: datetime
    next_followup_at: datetime | None = None


class CustomerFollowupCreate(CustomerFollowupBase):
    pass


class CustomerFollowupUpdate(BaseModel):
    contact_id: UUID | None = None
    followup_type: str | None = Field(default=None, max_length=32)
    content: str | None = None
    followup_at: datetime | None = None
    next_followup_at: datetime | None = None


class CustomerFollowupRead(CustomerFollowupBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}
