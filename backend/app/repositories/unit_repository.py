from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.unit import Unit
from app.repositories.common_repository import get_by_id, paginate_query


async def create_unit(db: AsyncSession, data: dict) -> Unit:
    obj = Unit(**data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_units(db: AsyncSession, page: int, page_size: int, q: str | None) -> tuple[int, list[Unit]]:
    return await paginate_query(db, Unit, page, page_size, q, [Unit.code, Unit.name])


async def get_unit(db: AsyncSession, object_id: UUID) -> Unit | None:
    return await get_by_id(db, Unit, object_id)


async def update_unit(db: AsyncSession, obj: Unit, data: dict) -> Unit:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_unit(db: AsyncSession, obj: Unit) -> Unit:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj
