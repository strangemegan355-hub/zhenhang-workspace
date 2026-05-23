from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.user import User


def _user_load_options():
    return (
        selectinload(User.roles).selectinload(Role.permissions),
        selectinload(User.department),
    )


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(User.username == username).options(*_user_load_options())
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    stmt = select(User).where(User.id == user_id).options(*_user_load_options())
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
