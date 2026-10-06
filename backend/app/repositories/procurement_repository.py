from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.procurement_entry import ProcurementEntry
from app.repositories.common_repository import get_by_id, paginate_query


async def count_request_no_prefix(db: AsyncSession, prefix: str) -> int:
    stmt = select(func.count()).select_from(ProcurementEntry).where(
        ProcurementEntry.request_no.like(f"{prefix}%"),
        ProcurementEntry.is_deleted.is_(False),
    )
    return int((await db.execute(stmt)).scalar_one())


async def generate_request_no(db: AsyncSession) -> str:
    prefix = f"PR-{date.today().strftime('%Y%m%d')}-"
    count = await count_request_no_prefix(db, prefix)
    return f"{prefix}{count + 1:03d}"


async def create_entry(db: AsyncSession, data: dict) -> ProcurementEntry:
    obj = ProcurementEntry(**data)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_entries(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    *,
    project_id: UUID | None = None,
    status: str | None = None,
    predicate=None,
):
    extra_filters = []
    if predicate is not None:
        extra_filters.append(predicate)
    if project_id is not None:
        extra_filters.append(ProcurementEntry.project_id == project_id)
    if status:
        extra_filters.append(ProcurementEntry.status == status)
    return await paginate_query(
        db,
        ProcurementEntry,
        page,
        page_size,
        q,
        [ProcurementEntry.request_no, ProcurementEntry.remark],
        extra_filters=extra_filters,
    )


async def get_entry(db: AsyncSession, object_id: UUID, predicate=None) -> ProcurementEntry | None:
    return await get_by_id(db, ProcurementEntry, object_id, predicate)


async def update_entry(db: AsyncSession, obj: ProcurementEntry, data: dict) -> ProcurementEntry:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_entry(db: AsyncSession, obj: ProcurementEntry) -> ProcurementEntry:
    obj.is_deleted = True
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_arrived_not_transferred(
    db: AsyncSession, predicate=None
) -> list[ProcurementEntry]:
    stmt = select(ProcurementEntry).where(
        ProcurementEntry.is_deleted.is_(False),
        ProcurementEntry.status == "arrived",
        ProcurementEntry.transferred_to_actual.is_(False),
    )
    if predicate is not None:
        stmt = stmt.where(predicate)
    return list((await db.execute(stmt)).scalars().all())
