from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fieldwork_record import FieldworkRecord
from app.repositories.common_repository import get_by_id, paginate_query

_PREFIX_BY_TYPE = {
    "repair": "RPR",
    "shortage": "SHR",
    "loading": "LOD",
}


async def count_record_no_prefix(db: AsyncSession, prefix: str) -> int:
    stmt = select(func.count()).select_from(FieldworkRecord).where(
        FieldworkRecord.record_no.like(f"{prefix}%"),
        FieldworkRecord.is_deleted.is_(False),
    )
    return int((await db.execute(stmt)).scalar_one())


async def generate_record_no(db: AsyncSession, record_type: str) -> str:
    code = _PREFIX_BY_TYPE.get(record_type, "FLD")
    prefix = f"{code}-{date.today().strftime('%Y%m%d')}-"
    count = await count_record_no_prefix(db, prefix)
    return f"{prefix}{count + 1:03d}"


async def create_record(db: AsyncSession, data: dict) -> FieldworkRecord:
    obj = FieldworkRecord(**data)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_records(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    *,
    record_type: str | None = None,
    status: str | None = None,
    project_id: UUID | None = None,
):
    extra_filters = []
    if record_type:
        extra_filters.append(FieldworkRecord.record_type == record_type)
    if status:
        extra_filters.append(FieldworkRecord.status == status)
    if project_id is not None:
        extra_filters.append(FieldworkRecord.project_id == project_id)
    return await paginate_query(
        db,
        FieldworkRecord,
        page,
        page_size,
        q,
        [FieldworkRecord.record_no, FieldworkRecord.headline, FieldworkRecord.reporter_name, FieldworkRecord.remark],
        extra_filters=extra_filters,
    )


async def get_record(db: AsyncSession, object_id: UUID) -> FieldworkRecord | None:
    return await get_by_id(db, FieldworkRecord, object_id)


async def update_record(db: AsyncSession, obj: FieldworkRecord, data: dict) -> FieldworkRecord:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_record(db: AsyncSession, obj: FieldworkRecord) -> FieldworkRecord:
    obj.is_deleted = True
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def count_by_type(db: AsyncSession) -> dict[str, int]:
    stmt = (
        select(FieldworkRecord.record_type, func.count())
        .where(FieldworkRecord.is_deleted.is_(False))
        .group_by(FieldworkRecord.record_type)
    )
    rows = (await db.execute(stmt)).all()
    return {record_type: int(count) for record_type, count in rows}


async def count_open_shortages(db: AsyncSession) -> int:
    stmt = select(func.count()).select_from(FieldworkRecord).where(
        FieldworkRecord.is_deleted.is_(False),
        FieldworkRecord.record_type == "shortage",
        FieldworkRecord.status.in_(("reported", "acknowledged")),
    )
    return int((await db.execute(stmt)).scalar_one())
