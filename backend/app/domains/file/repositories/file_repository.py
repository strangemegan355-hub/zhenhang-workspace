from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file_center import FileObject, FilePreviewCache, FileRelation


async def create_file_object(db: AsyncSession, data: dict, *, autocommit: bool = True) -> FileObject:
    obj = FileObject(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def create_file_relation(db: AsyncSession, data: dict, *, autocommit: bool = True) -> FileRelation:
    obj = FileRelation(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def create_preview_cache(db: AsyncSession, data: dict, *, autocommit: bool = True) -> FilePreviewCache:
    obj = FilePreviewCache(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def get_preview_cache(db: AsyncSession, cache_key: str) -> FilePreviewCache | None:
    stmt = select(FilePreviewCache).where(FilePreviewCache.cache_key == cache_key, FilePreviewCache.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_file_object(db: AsyncSession, file_id: UUID) -> FileObject | None:
    stmt = select(FileObject).where(FileObject.id == file_id, FileObject.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_file_objects(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    q: str | None,
    category: str | None,
    created_by: UUID | None = None,
):
    filters = [FileObject.is_deleted.is_(False)]
    if created_by is not None:
        filters.append(FileObject.created_by == created_by)
    if category:
        filters.append(FileObject.category == category)
    if q:
        like_key = f"%{q.strip()}%"
        filters.append(
            or_(cast(FileObject.file_name, String).ilike(like_key), cast(FileObject.object_name, String).ilike(like_key))
        )
    count_stmt = select(func.count()).select_from(FileObject).where(*filters)
    total = int((await db.execute(count_stmt)).scalar_one())
    stmt = (
        select(FileObject)
        .where(*filters)
        .order_by(FileObject.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await db.execute(stmt)).scalars().all())
    return total, items
