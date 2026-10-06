import asyncio
import os

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.department import Department
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


MIN_PASSWORD_LENGTH = 12


def _required_password() -> str:
    """Read the bootstrap password from the environment; there is no default.

    This credential is the root of every other permission in the system, so it is never taken
    from a literal in this file. Generate one with:
      python -c "import secrets; print(secrets.token_urlsafe(18))"
    """
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    if not password.strip():
        raise SystemExit(
            "BOOTSTRAP_ADMIN_PASSWORD is required and has no default. Generate one with: "
            'python -c "import secrets; print(secrets.token_urlsafe(18))"'
        )
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(
            f"BOOTSTRAP_ADMIN_PASSWORD must be at least {MIN_PASSWORD_LENGTH} characters"
        )
    return password


async def _get_or_create_department(db, code: str, name: str, description: str) -> Department:
    existing = (
        await db.execute(select(Department).where(Department.code == code))
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    department = Department(name=name, code=code, parent_id=None, sort_order=0, description=description)
    db.add(department)
    await db.flush()
    print(f"+ department {code} ({name})")
    return department


async def _get_or_create_permission(db, code: str, name: str, resource: str, action: str) -> Permission:
    existing = (
        await db.execute(select(Permission).where(Permission.code == code))
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    permission = Permission(
        name=name, code=code, resource=resource, action=action, description="RBAC demo permission"
    )
    db.add(permission)
    await db.flush()
    print(f"+ permission {code}")
    return permission


async def _get_or_create_role(
    db, code: str, name: str, description: str, permission: Permission
) -> Role:
    """Return the role, with `permission` attached.

    The attachment happens inside the branch because the two branches behave differently and only one of them
    may touch the collection: a role created here is still transient when the permission is appended, so its
    `permissions` is a plain empty list; a role that already exists had its collection loaded by selectinload.
    Appending to a *persistent* role with an unloaded collection raises MissingGreenlet, which is what an
    earlier attempt at this fix did.
    """
    existing = (
        await db.execute(select(Role).where(Role.code == code).options(selectinload(Role.permissions)))
    ).scalar_one_or_none()
    if existing is not None:
        if permission not in existing.permissions:
            existing.permissions.append(permission)
        return existing

    role = Role(name=name, code=code, description=description, is_system=True)
    role.permissions.append(permission)
    db.add(role)
    await db.flush()
    print(f"+ role {code} ({name})")
    return role


async def bootstrap() -> None:
    username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin")
    password = _required_password()

    async with AsyncSessionLocal() as db:
        existing = (
            await db.execute(select(User).where(User.username == username))
        ).scalar_one_or_none()
        if existing is not None:
            # Say so. This is step 1 of the acceptance guide and an operator re-runs it; silence would leave
            # them unable to tell whether the account already existed — and it would not say that the
            # BOOTSTRAP_ADMIN_PASSWORD they just supplied was **not** applied.
            print(
                f"~ admin {username} already exists; the supplied password was not applied "
                "(delete the account or change it through the admin API)"
            )
            return

        department = await _get_or_create_department(db, "ROOT", "总部", "Bootstrap department")
        permission = await _get_or_create_permission(
            db, "system:user:read", "用户读取", "system:user", "read"
        )
        role = await _get_or_create_role(db, "admin", "系统管理员", "Bootstrap role", permission)

        admin = User(
            username=username,
            # Username-derived so a second administrator does not collide on the unique email index while
            # the documented path is unchanged: for `admin` this is still admin@example.com.
            email=os.getenv("BOOTSTRAP_ADMIN_EMAIL", f"{username}@example.com"),
            hashed_password=get_password_hash(password),
            full_name="系统管理员",
            is_active=True,
            is_superuser=True,
            department_id=department.id,
        )
        admin.roles.append(role)
        db.add(admin)
        await db.commit()
        print(f"+ admin {username} created with role 'admin'")


def main() -> None:
    asyncio.run(bootstrap())


if __name__ == "__main__":
    main()
