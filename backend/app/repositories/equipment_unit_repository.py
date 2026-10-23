from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.equipment_unit import EquipmentUnit


async def list_equipment_units(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    build_status: str | None = None,
    machine_id: UUID | None = None,
    customer_id: UUID | None = None,
) -> tuple[list[EquipmentUnit], int]:
    stmt = (
        select(EquipmentUnit)
        .options(joinedload(EquipmentUnit.machine), joinedload(EquipmentUnit.customer))
        .where(EquipmentUnit.is_deleted == False)
    )
    count_stmt = select(func.count(EquipmentUnit.id)).where(EquipmentUnit.is_deleted == False)

    if q:
        stmt = stmt.where(EquipmentUnit.serial_number.ilike(f"%{q}%"))
        count_stmt = count_stmt.where(EquipmentUnit.serial_number.ilike(f"%{q}%"))
    if build_status:
        stmt = stmt.where(EquipmentUnit.build_status == build_status)
        count_stmt = count_stmt.where(EquipmentUnit.build_status == build_status)
    if machine_id:
        stmt = stmt.where(EquipmentUnit.machine_id == machine_id)
        count_stmt = count_stmt.where(EquipmentUnit.machine_id == machine_id)
    if customer_id:
        stmt = stmt.where(EquipmentUnit.customer_id == customer_id)
        count_stmt = count_stmt.where(EquipmentUnit.customer_id == customer_id)

    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(EquipmentUnit.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(stmt)).unique().scalars().all())
    return items, total


async def get_equipment_unit_by_id(db: AsyncSession, unit_id: UUID) -> EquipmentUnit | None:
    stmt = (
        select(EquipmentUnit)
        .options(joinedload(EquipmentUnit.machine), joinedload(EquipmentUnit.customer))
        .where(EquipmentUnit.id == unit_id, EquipmentUnit.is_deleted == False)
    )
    return (await db.execute(stmt)).unique().scalar_one_or_none()


async def get_equipment_unit_by_serial(db: AsyncSession, serial_number: str) -> EquipmentUnit | None:
    stmt = select(EquipmentUnit).where(
        EquipmentUnit.serial_number == serial_number, EquipmentUnit.is_deleted == False
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_equipment_unit(db: AsyncSession, data: dict, user_id: UUID) -> EquipmentUnit:
    unit = EquipmentUnit(created_by=user_id, is_deleted=False, **data)
    db.add(unit)
    await db.flush()
    await db.commit()
    return unit


async def update_equipment_unit(db: AsyncSession, unit: EquipmentUnit, data: dict) -> EquipmentUnit:
    for key, value in data.items():
        if value is not None:
            setattr(unit, key, value)
    await db.flush()
    await db.commit()
    return unit
