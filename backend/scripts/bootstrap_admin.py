import asyncio
import os

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.department import Department
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


async def bootstrap() -> None:
    username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin")
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "Admin@123456")

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none() is not None:
            return

        dept = Department(name="总部", code="ROOT", parent_id=None, sort_order=0, description="Bootstrap department")
        db.add(dept)
        await db.flush()

        perm_read = Permission(
            name="用户读取",
            code="system:user:read",
            resource="system:user",
            action="read",
            description="RBAC demo permission",
        )
        db.add(perm_read)
        await db.flush()

        role_admin = Role(
            name="系统管理员",
            code="admin",
            description="Bootstrap role",
            is_system=True,
        )
        role_admin.permissions.append(perm_read)
        db.add(role_admin)
        await db.flush()

        admin = User(
            username=username,
            email=os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com"),
            hashed_password=get_password_hash(password),
            full_name="系统管理员",
            is_active=True,
            is_superuser=True,
            department_id=dept.id,
        )
        admin.roles.append(role_admin)
        db.add(admin)

        await db.commit()


def main() -> None:
    asyncio.run(bootstrap())


if __name__ == "__main__":
    main()
