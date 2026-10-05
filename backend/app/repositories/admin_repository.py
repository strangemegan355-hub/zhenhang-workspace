from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.models.permission import Permission
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User

# The admin plane touches five entities that share one shape, so their data access lives in a
# single module instead of five near-identical ones. The organisation and RBAC tables have no
# soft-delete column, so `common_repository.paginate_query` (which filters `is_deleted`) does
# not apply here; tenants do have it and are filtered explicitly.


def role_load_options() -> tuple[Any, ...]:
    return (selectinload(Role.permissions),)


def user_load_options() -> tuple[Any, ...]:
    return (selectinload(User.roles).selectinload(Role.permissions), selectinload(User.department))


async def _paginate(
    db: AsyncSession,
    model: Any,
    page: int,
    page_size: int,
    q: str | None,
    search_fields: Sequence[Any],
    extra_filters: Sequence[Any] = (),
    load_options: Sequence[Any] = (),
) -> tuple[int, list[Any]]:
    filters = list(extra_filters)
    if q and q.strip():
        keyword = f"%{q.strip()}%"
        conditions = [cast(field, String).ilike(keyword) for field in search_fields]
        if conditions:
            filters.append(or_(*conditions))

    count_stmt = select(func.count()).select_from(model).where(*filters)
    total = int((await db.execute(count_stmt)).scalar_one())

    stmt = (
        select(model)
        .where(*filters)
        .order_by(model.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if load_options:
        stmt = stmt.options(*load_options)
    items = list((await db.execute(stmt)).scalars().all())
    return total, items


async def create(db: AsyncSession, instance: Any) -> Any:
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance


async def save(db: AsyncSession, instance: Any, load_options: Sequence[Any] = ()) -> Any:
    await db.commit()
    if load_options:
        stmt = select(type(instance)).where(type(instance).id == instance.id).options(*load_options)
        reloaded = (await db.execute(stmt)).scalar_one()
        return reloaded
    await db.refresh(instance)
    return instance


# ------------------------------------------------------------------------------- roles


async def list_roles(db: AsyncSession, page: int, page_size: int, q: str | None) -> tuple[int, list[Role]]:
    return await _paginate(
        db, Role, page, page_size, q, (Role.name, Role.code, Role.description), load_options=role_load_options()
    )


async def get_role(db: AsyncSession, role_id: UUID) -> Role | None:
    stmt = select(Role).where(Role.id == role_id).options(*role_load_options())
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_role_by_code(db: AsyncSession, code: str) -> Role | None:
    stmt = select(Role).where(Role.code == code).options(*role_load_options())
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_roles_by_codes(db: AsyncSession, codes: Sequence[str]) -> list[Role]:
    if not codes:
        return []
    stmt = select(Role).where(Role.code.in_(list(codes))).options(*role_load_options())
    return list((await db.execute(stmt)).scalars().all())


# ------------------------------------------------------------------------- permissions


async def list_permissions(
    db: AsyncSession, page: int, page_size: int, q: str | None
) -> tuple[int, list[Permission]]:
    return await _paginate(
        db, Permission, page, page_size, q, (Permission.code, Permission.name, Permission.resource)
    )


async def get_permissions_by_codes(db: AsyncSession, codes: Sequence[str]) -> list[Permission]:
    if not codes:
        return []
    stmt = select(Permission).where(Permission.code.in_(list(codes)))
    return list((await db.execute(stmt)).scalars().all())


# ------------------------------------------------------------------------- departments


async def list_departments(db: AsyncSession) -> list[Department]:
    stmt = select(Department).order_by(Department.sort_order.asc(), Department.code.asc())
    return list((await db.execute(stmt)).scalars().all())


async def get_department(db: AsyncSession, department_id: UUID) -> Department | None:
    return (await db.execute(select(Department).where(Department.id == department_id))).scalar_one_or_none()


async def get_department_by_code(db: AsyncSession, code: str) -> Department | None:
    return (await db.execute(select(Department).where(Department.code == code))).scalar_one_or_none()


# ----------------------------------------------------------------------------- tenants


async def list_tenants(db: AsyncSession, page: int, page_size: int, q: str | None) -> tuple[int, list[Tenant]]:
    return await _paginate(
        db,
        Tenant,
        page,
        page_size,
        q,
        (Tenant.code, Tenant.name),
        extra_filters=(Tenant.is_deleted.is_(False),),
    )


async def get_tenant(db: AsyncSession, tenant_id: UUID) -> Tenant | None:
    stmt = select(Tenant).where(Tenant.id == tenant_id, Tenant.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_tenant_by_code(db: AsyncSession, code: str) -> Tenant | None:
    stmt = select(Tenant).where(Tenant.code == code, Tenant.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


# ------------------------------------------------------------------------------- users


async def list_users(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    department_id: UUID | None = None,
) -> tuple[int, list[User]]:
    extra = (User.department_id == department_id,) if department_id is not None else ()
    return await _paginate(
        db,
        User,
        page,
        page_size,
        q,
        (User.username, User.email, User.full_name, User.phone),
        extra_filters=extra,
        load_options=user_load_options(),
    )


async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    stmt = select(User).where(User.id == user_id).options(*user_load_options())
    return (await db.execute(stmt)).scalar_one_or_none()
