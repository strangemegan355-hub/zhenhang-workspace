from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material
from app.repositories.common_repository import get_by_id, paginate_query


async def create_material(db: AsyncSession, data: dict) -> Material:
    obj = Material(**data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_materials(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    category_id: UUID | None = None,
) -> tuple[int, list[Material]]:
    extra = [Material.category_id == category_id] if category_id else []
    return await paginate_query(db, Material, page, page_size, q, [Material.code, Material.name, Material.spec], extra)


async def get_material(db: AsyncSession, object_id: UUID) -> Material | None:
    return await get_by_id(db, Material, object_id)


async def update_material(db: AsyncSession, obj: Material, data: dict) -> Material:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_material(db: AsyncSession, obj: Material) -> Material:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj
