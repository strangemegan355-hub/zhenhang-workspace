from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material_category import MaterialCategory
from app.repositories.common_repository import get_by_id, paginate_query


async def create_material_category(db: AsyncSession, data: dict) -> MaterialCategory:
    obj = MaterialCategory(**data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_material_categories(
    db: AsyncSession, page: int, page_size: int, q: str | None
) -> tuple[int, list[MaterialCategory]]:
    return await paginate_query(db, MaterialCategory, page, page_size, q, [MaterialCategory.code, MaterialCategory.name])


async def get_material_category(db: AsyncSession, object_id: UUID) -> MaterialCategory | None:
    return await get_by_id(db, MaterialCategory, object_id)


async def update_material_category(db: AsyncSession, obj: MaterialCategory, data: dict) -> MaterialCategory:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_material_category(db: AsyncSession, obj: MaterialCategory) -> MaterialCategory:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj
