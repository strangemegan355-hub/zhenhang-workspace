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


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    department_id: UUID | None = None
    role_codes: list[str] = Field(default_factory=list, max_length=50)
    # is_superuser is deliberately absent: elevation is not something an API call can request.


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    department_id: UUID | None = None
    is_active: bool | None = None


class UserRoleUpdate(BaseModel):
    role_codes: list[str] = Field(default_factory=list, max_length=50)


class UserAdminRead(BaseModel):
    id: UUID
    username: str
    email: EmailStr | None = None
    full_name: str | None = None
    phone: str | None = None
    is_active: bool
    is_superuser: bool
    department_id: UUID | None = None
    role_codes: list[str] = Field(default_factory=list)

    @classmethod
    def from_user(cls, user) -> "UserAdminRead":
        # Field list is explicit on purpose: hashed_password must never be serialisable.
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            department_id=user.department_id,
            role_codes=sorted(role.code for role in user.roles),
        )
