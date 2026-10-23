from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import collect_permission_codes
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories import admin_repository as repo
from app.repositories.user_repository import get_user_by_username
from app.schemas.admin import DepartmentRead, PermissionRead, RoleRead, TenantRead
from app.schemas.common import PageResponse
from app.schemas.common import page_response as _page
from app.schemas.user import UserAdminRead
from app.services.audit_service import write_audit_log

# The admin plane is the only place that changes who may do what, so every mutation here is
# audited, and the two association-writing operations carry their own escalation guards. The
# route-level permission codes already restrict these calls to the superuser in the shipped
# trial catalogue; the guards below are defence in depth for the day an operator delegates a
# code such as system:role:assign to somebody else.

SYSTEM_ROLE_CODES = frozenset({"admin"})

def _is_superuser(user: User | None) -> bool:
    return bool(user is not None and getattr(user, "is_superuser", False))

def _effective_codes(user: User) -> set[str]:
    return collect_permission_codes(user)

def _forbid(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

async def _audit(
    db: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: UUID | None,
    current_user: User,
    detail: str,
    payload: dict | None = None,
) -> None:
    await write_audit_log(
        db,
        module="system",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        created_by=current_user.id,
        detail=detail,
        payload=payload,
        autocommit=True,
    )

# ------------------------------------------------------------------------------- roles

async def list_roles(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, roles = await repo.list_roles(db, page, page_size, q)
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[RoleRead.from_role(role) for role in roles],
    )

async def get_role_or_404(db: AsyncSession, role_id: UUID) -> RoleRead:
    role = await repo.get_role(db, role_id)
    if role is None:
        raise _not_found("Role not found")
    return RoleRead.from_role(role)

async def create_role(db: AsyncSession, payload: dict, current_user: User) -> RoleRead:
    code = payload["code"]
    if await repo.get_role_by_code(db, code) is not None:
        raise _conflict(f"Role code already exists: {code}")
    # is_system is never client-controlled: only the seeding scripts mark a role as system.
    role = Role(
        name=payload["name"],
        code=code,
        description=payload.get("description"),
        data_scope=payload.get("data_scope") or "self",
        is_system=False,
    )
    role = await repo.create(db, role)
    await _audit(
        db,
        action="role.create",
        resource_type="role",
        resource_id=role.id,
        current_user=current_user,
        detail=f"Created role {code}",
        payload={"code": code, "data_scope": role.data_scope},
    )
    return RoleRead.from_role(role)

async def update_role(db: AsyncSession, role_id: UUID, payload: dict, current_user: User) -> RoleRead:
    role = await repo.get_role(db, role_id)
    if role is None:
        raise _not_found("Role not found")
    if role.is_system and not _is_superuser(current_user):
        raise _forbid("Only a superuser may modify a system role")
    changed: dict = {}
    for field in ("name", "description", "data_scope"):
        if field in payload and payload[field] is not None:
            setattr(role, field, payload[field])
            changed[field] = payload[field]
    role = await repo.save(db, role, load_options=repo.role_load_options())
    await _audit(
        db,
        action="role.update",
        resource_type="role",
        resource_id=role.id,
        current_user=current_user,
        detail=f"Updated role {role.code}",
        payload=changed,
    )
    return RoleRead.from_role(role)

async def set_role_permissions(
    db: AsyncSession, role_id: UUID, permission_codes: list[str], current_user: User
) -> RoleRead:
    role = await repo.get_role(db, role_id)
    if role is None:
        raise _not_found("Role not found")
    if role.is_system and not _is_superuser(current_user):
        raise _forbid("Only a superuser may change the permissions of a system role")

    wanted = sorted(set(permission_codes))
    permissions = await repo.get_permissions_by_codes(db, wanted)
    known = {permission.code for permission in permissions}
    unknown = sorted(set(wanted) - known)
    if unknown:
        raise _bad_request({"unknown_permission_codes": unknown})

    if not _is_superuser(current_user):
        # A non-superuser can never widen a role beyond what they already hold; otherwise the
        # assign permission would be a one-step route to full privilege.
        mine = _effective_codes(current_user)
        escalating = sorted(set(wanted) - mine)
        if escalating:
            raise _forbid({"missing_permissions": escalating})

    role.permissions = permissions
    role = await repo.save(db, role, load_options=repo.role_load_options())
    await _audit(
        db,
        action="role.permissions",
        resource_type="role",
        resource_id=role.id,
        current_user=current_user,
        detail=f"Set {len(wanted)} permission(s) on role {role.code}",
        payload={"permission_codes": wanted},
    )
    return RoleRead.from_role(role)

# ------------------------------------------------------------------------- permissions

async def list_permissions(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, permissions = await repo.list_permissions(db, page, page_size, q)
    return _page(total, page, page_size, permissions, PermissionRead)

# ------------------------------------------------------------------------- departments

async def list_departments(db: AsyncSession) -> list[DepartmentRead]:
    departments = await repo.list_departments(db)
    return [DepartmentRead.model_validate(item) for item in departments]

async def create_department(db: AsyncSession, payload: dict, current_user: User) -> DepartmentRead:
    code = payload["code"]
    if await repo.get_department_by_code(db, code) is not None:
        raise _conflict(f"Department code already exists: {code}")
    parent_id = payload.get("parent_id")
    if parent_id is not None and await repo.get_department(db, parent_id) is None:
        raise _bad_request("Parent department does not exist")
    department = Department(
        name=payload["name"],
        code=code,
        parent_id=parent_id,
        sort_order=payload.get("sort_order") or 0,
        description=payload.get("description"),
    )
    department = await repo.create(db, department)
    await _audit(
        db,
        action="department.create",
        resource_type="department",
        resource_id=department.id,
        current_user=current_user,
        detail=f"Created department {code}",
        payload={"code": code, "parent_id": str(parent_id) if parent_id else None},
    )
    return DepartmentRead.model_validate(department)

async def update_department(
    db: AsyncSession, department_id: UUID, payload: dict, current_user: User
) -> DepartmentRead:
    department = await repo.get_department(db, department_id)
    if department is None:
        raise _not_found("Department not found")

    if "parent_id" in payload:
        parent_id = payload["parent_id"]
        if parent_id is not None:
            if parent_id == department_id:
                raise _bad_request("A department cannot be its own parent")
            parent = await repo.get_department(db, parent_id)
            if parent is None:
                raise _bad_request("Parent department does not exist")
            # Walk up from the proposed parent: if this department appears, the move would
            # create a cycle and the tree would become unrenderable.
            seen: set[UUID] = set()
            cursor: Department | None = parent
            while cursor is not None and cursor.id not in seen:
                if cursor.id == department_id:
                    raise _bad_request("That parent would create a department cycle")
                seen.add(cursor.id)
                cursor = await repo.get_department(db, cursor.parent_id) if cursor.parent_id else None
        department.parent_id = parent_id

    changed: dict = {"parent_id": str(department.parent_id) if department.parent_id else None}
    for field in ("name", "sort_order", "description"):
        if field in payload and payload[field] is not None:
            setattr(department, field, payload[field])
            changed[field] = payload[field]

    department = await repo.save(db, department)
    await _audit(
        db,
        action="department.update",
        resource_type="department",
        resource_id=department.id,
        current_user=current_user,
        detail=f"Updated department {department.code}",
        payload=changed,
    )
    return DepartmentRead.model_validate(department)

# ----------------------------------------------------------------------------- tenants

async def list_tenants(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, tenants = await repo.list_tenants(db, page, page_size, q)
    return _page(total, page, page_size, tenants, TenantRead)

async def get_tenant_or_404(db: AsyncSession, tenant_id: UUID) -> TenantRead:
    tenant = await repo.get_tenant(db, tenant_id)
    if tenant is None:
        raise _not_found("Tenant not found")
    return TenantRead.model_validate(tenant)

async def create_tenant(db: AsyncSession, payload: dict, current_user: User) -> TenantRead:
    code = payload["code"]
    if await repo.get_tenant_by_code(db, code) is not None:
        raise _conflict(f"Tenant code already exists: {code}")
    tenant = Tenant(code=code, name=payload["name"], created_by=current_user.id)
    tenant = await repo.create(db, tenant)
    await _audit(
        db,
        action="tenant.create",
        resource_type="tenant",
        resource_id=tenant.id,
        current_user=current_user,
        detail=f"Created tenant {code}",
        payload={"code": code},
    )
    return TenantRead.model_validate(tenant)

async def update_tenant(db: AsyncSession, tenant_id: UUID, payload: dict, current_user: User) -> TenantRead:
    tenant = await repo.get_tenant(db, tenant_id)
    if tenant is None:
        raise _not_found("Tenant not found")
    changed: dict = {}
    for field in ("name", "is_active"):
        if field in payload and payload[field] is not None:
            setattr(tenant, field, payload[field])
            changed[field] = payload[field]
    tenant = await repo.save(db, tenant)
    await _audit(
        db,
        action="tenant.update",
        resource_type="tenant",
        resource_id=tenant.id,
        current_user=current_user,
        detail=f"Updated tenant {tenant.code}",
        payload=changed,
    )
    return TenantRead.model_validate(tenant)

# ------------------------------------------------------------------------------- users

async def list_users(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    department_id: UUID | None,
    current_user: User,
) -> PageResponse:
    # Object-level scope: an ordinary administrator sees only their own department, and cannot
    # widen the query by asking for somebody else's.
    if not _is_superuser(current_user):
        if department_id is not None and department_id != current_user.department_id:
            raise _forbid("You may only list users of your own department")
        department_id = current_user.department_id
    total, users = await repo.list_users(db, page, page_size, q, department_id)
    return _page(total, page, page_size, users, UserAdminRead)

async def get_user_or_404(db: AsyncSession, user_id: UUID, current_user: User) -> UserAdminRead:
    user = await repo.get_user(db, user_id)
    if user is None:
        raise _not_found("User not found")
    if (
        not _is_superuser(current_user)
        and user.id != current_user.id
        and user.department_id != current_user.department_id
    ):
        raise _forbid("You may only read users of your own department")
    return UserAdminRead.from_user(user)

async def _resolve_roles(db: AsyncSession, role_codes: list[str], current_user: User) -> list[Role]:
    wanted = sorted(set(role_codes))
    roles = await repo.get_roles_by_codes(db, wanted)
    known = {role.code for role in roles}
    unknown = sorted(set(wanted) - known)
    if unknown:
        raise _bad_request({"unknown_role_codes": unknown})
    if _is_superuser(current_user):
        return roles
    blocked = sorted(role.code for role in roles if role.code in SYSTEM_ROLE_CODES or role.is_system)
    if blocked:
        raise _forbid({"roles_requiring_superuser": blocked})
    mine = _effective_codes(current_user)
    escalating = sorted({permission.code for role in roles for permission in role.permissions} - mine)
    if escalating:
        raise _forbid({"missing_permissions": escalating})
    return roles

async def create_user(db: AsyncSession, payload: dict, current_user: User) -> UserAdminRead:
    username = payload["username"]
    if await get_user_by_username(db, username) is not None:
        raise _conflict(f"Username already taken: {username}")
    email = payload.get("email")
    if email:
        existing = await repo.list_users(db, 1, 1, email)
        if any(user.email == email for user in existing[1]):
            raise _conflict(f"Email already taken: {email}")

    department_id = payload.get("department_id")
    if department_id is not None and await repo.get_department(db, department_id) is None:
        raise _bad_request("Department does not exist")
    if not _is_superuser(current_user):
        # Same rule as listing: nobody creates an account outside their own department.
        if department_id is not None and department_id != current_user.department_id:
            raise _forbid("You may only create users in your own department")
        department_id = current_user.department_id

    roles = await _resolve_roles(db, payload.get("role_codes") or [], current_user)

    user = User(
        username=username,
        email=email,
        full_name=payload.get("full_name"),
        phone=payload.get("phone"),
        hashed_password=get_password_hash(payload["password"]),
        department_id=department_id,
        is_active=True,
        is_superuser=False,
    )
    user.roles = roles
    user = await repo.create(db, user)
    user = await repo.get_user(db, user.id) or user
    await _audit(
        db,
        action="user.create",
        resource_type="user",
        resource_id=user.id,
        current_user=current_user,
        detail=f"Created user {username}",
        # The password never reaches the audit payload.
        payload={"username": username, "role_codes": sorted(role.code for role in roles)},
    )
    return UserAdminRead.from_user(user)

async def update_user(
    db: AsyncSession, user_id: UUID, payload: dict, current_user: User
) -> UserAdminRead:
    user = await repo.get_user(db, user_id)
    if user is None:
        raise _not_found("User not found")
    if user.is_superuser and not _is_superuser(current_user):
        raise _forbid("Only a superuser may modify a superuser account")
    if (
        not _is_superuser(current_user)
        and user.id != current_user.id
        and user.department_id != current_user.department_id
    ):
        raise _forbid("You may only modify users of your own department")
    if payload.get("is_active") is False and user.id == current_user.id:
        raise _bad_request("You cannot deactivate your own account")

    email = payload.get("email")
    if email and email != user.email:
        existing = await repo.list_users(db, 1, 1, email)
        if any(other.email == email and other.id != user.id for other in existing[1]):
            raise _conflict(f"Email already taken: {email}")

    changed: dict = {}
    for field in ("email", "full_name", "phone", "is_active"):
        if field in payload and payload[field] is not None:
            setattr(user, field, payload[field])
            changed[field] = payload[field]
    if "department_id" in payload and payload["department_id"] is not None:
        if await repo.get_department(db, payload["department_id"]) is None:
            raise _bad_request("Department does not exist")
        if not _is_superuser(current_user) and payload["department_id"] != current_user.department_id:
            raise _forbid("You may only move users within your own department")
        user.department_id = payload["department_id"]
        changed["department_id"] = str(user.department_id)

    user = await repo.save(db, user, load_options=repo.user_load_options())
    await _audit(
        db,
        action="user.update",
        resource_type="user",
        resource_id=user.id,
        current_user=current_user,
        detail=f"Updated user {user.username}",
        payload=changed,
    )
    return UserAdminRead.from_user(user)

async def set_user_roles(
    db: AsyncSession, user_id: UUID, role_codes: list[str], current_user: User
) -> UserAdminRead:
    user = await repo.get_user(db, user_id)
    if user is None:
        raise _not_found("User not found")
    if user.is_superuser and not _is_superuser(current_user):
        raise _forbid("Only a superuser may modify a superuser account")
    if user.id == current_user.id and not _is_superuser(current_user):
        raise _forbid("You cannot change your own roles")
    if not _is_superuser(current_user) and user.department_id != current_user.department_id:
        raise _forbid("You may only assign roles to users of your own department")

    roles = await _resolve_roles(db, role_codes, current_user)
    user.roles = roles
    user = await repo.save(db, user, load_options=repo.user_load_options())
    await _audit(
        db,
        action="user.roles",
        resource_type="user",
        resource_id=user.id,
        current_user=current_user,
        detail=f"Set roles for {user.username}",
        payload={"role_codes": sorted(role.code for role in roles)},
    )
    return UserAdminRead.from_user(user)
