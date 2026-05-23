from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_config import SystemConfig


async def create_config(db: AsyncSession, data: dict, *, autocommit: bool = True) -> SystemConfig:
    obj = SystemConfig(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def update_config(db: AsyncSession, obj: SystemConfig, data: dict, *, autocommit: bool = True) -> SystemConfig:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def get_config_by_key(db: AsyncSession, key: str) -> SystemConfig | None:
    stmt = select(SystemConfig).where(SystemConfig.key == key, SystemConfig.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_config_by_id(db: AsyncSession, object_id: UUID) -> SystemConfig | None:
    stmt = select(SystemConfig).where(SystemConfig.id == object_id, SystemConfig.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_configs(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    q: str | None,
    group: str | None,
    created_by: UUID | None = None,
):
    filters = [SystemConfig.is_deleted.is_(False)]
    if created_by is not None:
        filters.append(SystemConfig.created_by == created_by)
    if group:
        filters.append(SystemConfig.group == group)
    if q:
        like_key = f"%{q.strip()}%"
        filters.append(or_(cast(SystemConfig.key, String).ilike(like_key), cast(SystemConfig.value, String).ilike(like_key)))
    count_stmt = select(func.count()).select_from(SystemConfig).where(*filters)
    total = int((await db.execute(count_stmt)).scalar_one())
    stmt = (
        select(SystemConfig)
        .where(*filters)
        .order_by(SystemConfig.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await db.execute(stmt)).scalars().all())
    return total, items
