from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier
from app.repositories.common_repository import get_by_id, paginate_query


async def create_supplier(db: AsyncSession, data: dict) -> Supplier:
    obj = Supplier(**data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_suppliers(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
) -> tuple[int, list[Supplier]]:
    return await paginate_query(
        db,
        Supplier,
        page,
        page_size,
        q,
        [Supplier.code, Supplier.name, Supplier.contact_name, Supplier.phone],
    )


async def get_supplier(db: AsyncSession, object_id: UUID) -> Supplier | None:
    return await get_by_id(db, Supplier, object_id)


async def update_supplier(db: AsyncSession, obj: Supplier, data: dict) -> Supplier:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_supplier(db: AsyncSession, obj: Supplier) -> Supplier:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj
