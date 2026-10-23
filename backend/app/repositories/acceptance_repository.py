from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.acceptance import AcceptanceRecord, AcceptanceTemplate, PunchListItem

# ── Templates ──

async def list_templates(db: AsyncSession, machine_id: UUID | None = None) -> list[AcceptanceTemplate]:
    stmt = (
        select(AcceptanceTemplate)
        .where(AcceptanceTemplate.is_deleted == False)
        .order_by(AcceptanceTemplate.created_at.desc())
    )
    if machine_id is not None:
        stmt = stmt.where(AcceptanceTemplate.machine_id == machine_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_template_by_id(db: AsyncSession, template_id: UUID) -> AcceptanceTemplate | None:
    stmt = select(AcceptanceTemplate).where(
        AcceptanceTemplate.id == template_id,
        AcceptanceTemplate.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_template(db: AsyncSession, data: dict, user_id: UUID) -> AcceptanceTemplate:
    t = AcceptanceTemplate(created_by=user_id, is_deleted=False, **data)
    db.add(t)
    await db.flush()
    await db.commit()
    return t


async def update_template(db: AsyncSession, template: AcceptanceTemplate, data: dict) -> AcceptanceTemplate:
    for key, value in data.items():
        if value is not None:
            setattr(template, key, value)
    await db.flush()
    await db.commit()
    return template


async def delete_template(db: AsyncSession, template: AcceptanceTemplate) -> None:
    template.is_deleted = True
    await db.flush()
    await db.commit()


# ── Records ──

async def list_records(db: AsyncSession, equipment_unit_id: UUID) -> list[AcceptanceRecord]:
    stmt = (
        select(AcceptanceRecord)
        .options(joinedload(AcceptanceRecord.punch_items))
        .where(
            AcceptanceRecord.equipment_unit_id == equipment_unit_id,
            AcceptanceRecord.is_deleted == False,
        )
        .order_by(AcceptanceRecord.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.unique().scalars().all())


async def get_record_by_id(db: AsyncSession, record_id: UUID) -> AcceptanceRecord | None:
    stmt = (
        select(AcceptanceRecord)
        .options(joinedload(AcceptanceRecord.punch_items))
        .where(AcceptanceRecord.id == record_id, AcceptanceRecord.is_deleted == False)
    )
    result = await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def create_record(db: AsyncSession, data: dict, user_id: UUID) -> AcceptanceRecord:
    r = AcceptanceRecord(created_by=user_id, is_deleted=False, **data)
    db.add(r)
    await db.flush()
    await db.commit()
    return r


async def update_record(db: AsyncSession, record: AcceptanceRecord, data: dict) -> AcceptanceRecord:
    for key, value in data.items():
        if value is not None:
            setattr(record, key, value)
    await db.flush()
    await db.commit()
    return record


async def delete_record(db: AsyncSession, record: AcceptanceRecord) -> None:
    record.is_deleted = True
    await db.flush()
    await db.commit()


# ── Punch items ──

async def get_punch_item_by_id(db: AsyncSession, item_id: UUID) -> PunchListItem | None:
    stmt = select(PunchListItem).where(
        PunchListItem.id == item_id, PunchListItem.is_deleted == False
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_punch_item(db: AsyncSession, record_id: UUID, data: dict, user_id: UUID) -> PunchListItem:
    p = PunchListItem(record_id=record_id, created_by=user_id, is_deleted=False, **data)
    db.add(p)
    await db.flush()
    await db.commit()
    return p


async def update_punch_item(db: AsyncSession, item: PunchListItem, data: dict) -> PunchListItem:
    for key, value in data.items():
        if value is not None:
            setattr(item, key, value)
    if data.get("status") == "resolved" and item.resolved_at is None:
        from datetime import datetime, timezone
        item.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    await db.commit()
    return item


async def delete_punch_item(db: AsyncSession, item: PunchListItem) -> None:
    item.is_deleted = True
    await db.flush()
    await db.commit()
