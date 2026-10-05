from uuid import UUID

from pydantic import BaseModel, Field

DATA_SCOPE_PATTERN = r"^(all|self|department|none)$"


class PermissionRead(BaseModel):
    id: UUID
    code: str
    name: str
    resource: str
    action: str
    description: str | None = None

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    description: str | None = None
    data_scope: str = Field(default="self", pattern=DATA_SCOPE_PATTERN)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None
    data_scope: str | None = Field(default=None, pattern=DATA_SCOPE_PATTERN)


class RoleRead(BaseModel):
    id: UUID
    name: str
    code: str
    description: str | None = None
    is_system: bool
    data_scope: str
    permission_codes: list[str] = Field(default_factory=list)

    @classmethod
    def from_role(cls, role) -> "RoleRead":
        # Permission codes, not ORM rows: the API contract stays stable if the association
        # object gains columns, and it never exposes the whole permission table by accident.
        return cls(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            is_system=role.is_system,
            data_scope=role.data_scope,
            permission_codes=sorted(permission.code for permission in role.permissions),
        )


class RolePermissionUpdate(BaseModel):
    permission_codes: list[str] = Field(default_factory=list, max_length=500)


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=64)
    parent_id: UUID | None = None
    sort_order: int = Field(default=0, ge=0)
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: UUID | None = None
    sort_order: int | None = Field(default=None, ge=0)
    description: str | None = None


class DepartmentRead(BaseModel):
    id: UUID
    name: str
    code: str
    parent_id: UUID | None = None
    sort_order: int
    description: str | None = None

    model_config = {"from_attributes": True}


class TenantCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=160)


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    is_active: bool | None = None


class TenantRead(BaseModel):
    id: UUID
    code: str
    name: str
    is_active: bool

    model_config = {"from_attributes": True}
