from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate_query(
    db: AsyncSession,
    model: Any,
    page: int,
    page_size: int,
    q: str | None = None,
    search_fields: Sequence[Any] = (),
    extra_filters: Sequence[Any] = (),
) -> tuple[int, list[Any]]:
    filters = [model.is_deleted.is_(False), *extra_filters]
    if q:
        keyword = f"%{q.strip()}%"
        search_conds = [cast(field, String).ilike(keyword) for field in search_fields]
        if search_conds:
            filters.append(or_(*search_conds))

    count_stmt = select(func.count()).select_from(model).where(*filters)
    total = int((await db.execute(count_stmt)).scalar_one())

    stmt = (
        select(model)
        .where(*filters)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(model.created_at.desc())
    )
    items = list((await db.execute(stmt)).scalars().all())
    return total, items


async def get_by_id(db: AsyncSession, model: Any, object_id: UUID) -> Any | None:
    stmt = select(model).where(model.id == object_id, model.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def soft_delete_by_id(db: AsyncSession, model: Any, object_id: UUID) -> bool:
    obj = await get_by_id(db, model, object_id)
    if obj is None:
        return False
    obj.is_deleted = True
    await db.commit()
    return True
