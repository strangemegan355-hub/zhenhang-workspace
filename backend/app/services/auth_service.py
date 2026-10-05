import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import get_user_by_username


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if user is None:
        return None
    valid = await asyncio.to_thread(verify_password, password, user.hashed_password)
    if not valid:
        return None
    return user
