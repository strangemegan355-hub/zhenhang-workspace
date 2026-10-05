from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import (
    Machine,
    MachineBom,
    MachineBomItem,
    MachineCategory,
    MachineImage,
    MachineParameter,
)
from app.repositories.common_repository import get_by_id, paginate_query


async def _create(db: AsyncSession, model, data: dict, *, autocommit: bool = True):
    obj = model(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def _update(db: AsyncSession, obj, data: dict, *, autocommit: bool = True):
    for key, value in data.items():
        setattr(obj, key, value)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def _soft_delete(db: AsyncSession, obj, *, autocommit: bool = True):
    obj.is_deleted = True
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def create_machine_category(db: AsyncSession, data: dict) -> MachineCategory:
    return await _create(db, MachineCategory, data)


async def list_machine_categories(db: AsyncSession, page: int, page_size: int, q: str | None):
    return await paginate_query(db, MachineCategory, page, page_size, q, [MachineCategory.code, MachineCategory.name])


async def get_machine_category(db: AsyncSession, object_id: UUID):
    return await get_by_id(db, MachineCategory, object_id)


async def update_machine_category(db: AsyncSession, obj: MachineCategory, data: dict):
    return await _update(db, obj, data)


async def soft_delete_machine_category(db: AsyncSession, obj: MachineCategory):
    return await _soft_delete(db, obj)


async def create_machine(db: AsyncSession, data: dict) -> Machine:
    return await _create(db, Machine, data)


async def list_machines(db: AsyncSession, page: int, page_size: int, q: str | None):
    return await paginate_query(
        db,
        Machine,
        page,
        page_size,
        q,
        [Machine.code, Machine.machine_code, Machine.name, Machine.model_no],
    )


async def get_machine(db: AsyncSession, object_id: UUID):
    return await get_by_id(db, Machine, object_id)


async def update_machine(db: AsyncSession, obj: Machine, data: dict):
    return await _update(db, obj, data)


async def soft_delete_machine(db: AsyncSession, obj: Machine):
    return await _soft_delete(db, obj)


async def create_machine_parameter(db: AsyncSession, data: dict) -> MachineParameter:
    return await _create(db, MachineParameter, data)


async def list_machine_parameters(db: AsyncSession, page: int, page_size: int, q: str | None, *, machine_id=None):
    extra = []
    if machine_id is not None:
        extra.append(MachineParameter.machine_id == machine_id)
    return await paginate_query(
        db,
        MachineParameter,
        page,
        page_size,
        q,
        [MachineParameter.param_key, MachineParameter.param_name, MachineParameter.value],
        extra,
    )


async def get_machine_parameter(db: AsyncSession, object_id: UUID):
    return await get_by_id(db, MachineParameter, object_id)


async def update_machine_parameter(db: AsyncSession, obj: MachineParameter, data: dict):
    return await _update(db, obj, data)


async def soft_delete_machine_parameter(db: AsyncSession, obj: MachineParameter):
    return await _soft_delete(db, obj)


async def create_machine_image(db: AsyncSession, data: dict) -> MachineImage:
    return await _create(db, MachineImage, data)


async def list_machine_images(db: AsyncSession, page: int, page_size: int, q: str | None, *, machine_id=None):
    extra = []
    if machine_id is not None:
        extra.append(MachineImage.machine_id == machine_id)
    return await paginate_query(db, MachineImage, page, page_size, q, [MachineImage.file_name, MachineImage.file_url], extra)


async def get_machine_image(db: AsyncSession, object_id: UUID):
    return await get_by_id(db, MachineImage, object_id)


async def update_machine_image(db: AsyncSession, obj: MachineImage, data: dict):
    return await _update(db, obj, data)


async def soft_delete_machine_image(db: AsyncSession, obj: MachineImage):
    return await _soft_delete(db, obj)


async def create_machine_bom(db: AsyncSession, data: dict, *, autocommit: bool = True) -> MachineBom:
    return await _create(db, MachineBom, data, autocommit=autocommit)


async def list_machine_boms(db: AsyncSession, page: int, page_size: int, q: str | None):
    return await paginate_query(db, MachineBom, page, page_size, q, [MachineBom.version, MachineBom.status])


async def get_machine_bom(db: AsyncSession, object_id: UUID):
    return await get_by_id(db, MachineBom, object_id)


async def update_machine_bom(db: AsyncSession, obj: MachineBom, data: dict, *, autocommit: bool = True):
    return await _update(db, obj, data, autocommit=autocommit)


async def soft_delete_machine_bom(db: AsyncSession, obj: MachineBom, *, autocommit: bool = True):
    return await _soft_delete(db, obj, autocommit=autocommit)


async def create_machine_bom_item(db: AsyncSession, data: dict, *, autocommit: bool = True) -> MachineBomItem:
    return await _create(db, MachineBomItem, data, autocommit=autocommit)


async def list_machine_bom_items(db: AsyncSession, page: int, page_size: int, q: str | None, *, bom_id=None):
    extra = []
    if bom_id is not None:
        extra.append(MachineBomItem.bom_id == bom_id)
    return await paginate_query(
        db,
        MachineBomItem,
        page,
        page_size,
        q,
        [MachineBomItem.item_code, MachineBomItem.item_name, MachineBomItem.spec],
        extra,
    )


async def get_machine_bom_item(db: AsyncSession, object_id: UUID):
    return await get_by_id(db, MachineBomItem, object_id)


async def update_machine_bom_item(db: AsyncSession, obj: MachineBomItem, data: dict, *, autocommit: bool = True):
    return await _update(db, obj, data, autocommit=autocommit)


async def soft_delete_machine_bom_item(db: AsyncSession, obj: MachineBomItem, *, autocommit: bool = True):
    return await _soft_delete(db, obj, autocommit=autocommit)


async def exists_machine_code(db: AsyncSession, machine_code: str, exclude_id: UUID | None = None) -> bool:
    stmt = select(Machine.id).where(Machine.machine_code == machine_code, Machine.is_deleted.is_(False))
    if exclude_id is not None:
        stmt = stmt.where(Machine.id != exclude_id)
    return (await db.execute(stmt.limit(1))).scalar_one_or_none() is not None


async def exists_machine_name(db: AsyncSession, name: str, exclude_id: UUID | None = None) -> bool:
    stmt = select(Machine.id).where(Machine.name == name, Machine.is_deleted.is_(False))
    if exclude_id is not None:
        stmt = stmt.where(Machine.id != exclude_id)
    return (await db.execute(stmt.limit(1))).scalar_one_or_none() is not None


async def count_machine_code_prefix(db: AsyncSession, prefix: str) -> int:
    stmt = select(func.count()).select_from(Machine).where(
        Machine.machine_code.like(f"{prefix}%"),
        Machine.is_deleted.is_(False),
    )
    return int((await db.execute(stmt)).scalar_one())


async def exists_bom_version(
    db: AsyncSession,
    machine_id: UUID,
    version: str,
    exclude_id: UUID | None = None,
) -> bool:
    stmt = select(MachineBom.id).where(
        MachineBom.machine_id == machine_id,
        MachineBom.version == version,
        MachineBom.is_deleted.is_(False),
    )
    if exclude_id is not None:
        stmt = stmt.where(MachineBom.id != exclude_id)
    return (await db.execute(stmt.limit(1))).scalar_one_or_none() is not None


async def deactivate_other_boms(db: AsyncSession, machine_id: UUID, active_bom_id: UUID) -> None:
    stmt = select(MachineBom).where(
        MachineBom.machine_id == machine_id,
        MachineBom.id != active_bom_id,
        MachineBom.is_deleted.is_(False),
        MachineBom.is_active.is_(True),
    )
    rows = (await db.execute(stmt)).scalars().all()
    for row in rows:
        row.is_active = False
    await db.flush()


async def recalculate_bom_total_cost(db: AsyncSession, bom_id: UUID) -> None:
    item_stmt = select(MachineBomItem).where(
        MachineBomItem.bom_id == bom_id,
        MachineBomItem.is_deleted.is_(False),
    )
    items = (await db.execute(item_stmt)).scalars().all()
    total = 0
    for item in items:
        line = item.quantity * item.unit_cost * (1 + item.loss_rate)
        item.line_total = line
        total += line
    bom = await get_machine_bom(db, bom_id)
    if bom is not None:
        bom.total_cost = total
    await db.flush()


async def get_machine_boms_by_ids(db: AsyncSession, ids: list[UUID]) -> list[MachineBom]:
    stmt = select(MachineBom).where(MachineBom.id.in_(ids), MachineBom.is_deleted.is_(False))
    return list((await db.execute(stmt)).scalars().all())
