from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RoleBrief(BaseModel):
    id: UUID
    code: str
    name: str

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    id: UUID
    username: str
    email: EmailStr | None = None
    full_name: str | None = None
    phone: str | None = None
    is_active: bool
    is_superuser: bool
    department_id: UUID | None = None
    roles: list[RoleBrief] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    data_scope: str = "self"

    model_config = {"from_attributes": True}
