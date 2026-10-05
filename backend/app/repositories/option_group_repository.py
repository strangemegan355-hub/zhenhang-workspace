from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.option_group import OptionGroup, OptionItem


async def list_option_groups(db: AsyncSession, machine_id: UUID) -> list[OptionGroup]:
    stmt = (
        select(OptionGroup)
        .options(joinedload(OptionGroup.items))
        .where(OptionGroup.machine_id == machine_id, OptionGroup.is_deleted == False)
        .order_by(OptionGroup.sort_order)
    )
    result = await db.execute(stmt)
    return list(result.unique().scalars().all())


async def get_option_group_by_id(db: AsyncSession, group_id: UUID) -> OptionGroup | None:
    stmt = (
        select(OptionGroup)
        .options(joinedload(OptionGroup.items))
        .where(OptionGroup.id == group_id, OptionGroup.is_deleted == False)
    )
    result = await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def create_option_group(db: AsyncSession, machine_id: UUID, data: dict, user_id: UUID) -> OptionGroup:
    group = OptionGroup(machine_id=machine_id, created_by=user_id, is_deleted=False, **data)
    db.add(group)
    await db.flush()
    await db.commit()
    return group


async def update_option_group(db: AsyncSession, group: OptionGroup, data: dict) -> OptionGroup:
    for key, value in data.items():
        if value is not None:
            setattr(group, key, value)
    await db.flush()
    await db.commit()
    return group


async def delete_option_group(db: AsyncSession, group: OptionGroup) -> None:
    group.is_deleted = True
    await db.flush()
    await db.commit()


async def get_option_item_by_id(db: AsyncSession, item_id: UUID) -> OptionItem | None:
    stmt = select(OptionItem).where(OptionItem.id == item_id, OptionItem.is_deleted == False)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_option_item(db: AsyncSession, group_id: UUID, data: dict, user_id: UUID) -> OptionItem:
    item = OptionItem(option_group_id=group_id, created_by=user_id, is_deleted=False, **data)
    db.add(item)
    await db.flush()
    await db.commit()
    return item


async def update_option_item(db: AsyncSession, item: OptionItem, data: dict) -> OptionItem:
    for key, value in data.items():
        if value is not None:
            setattr(item, key, value)
    await db.flush()
    await db.commit()
    return item


async def delete_option_item(db: AsyncSession, item: OptionItem) -> None:
    item.is_deleted = True
    await db.flush()
    await db.commit()


async def get_option_items_by_ids(db: AsyncSession, item_ids: list[UUID]) -> list[OptionItem]:
    stmt = (
        select(OptionItem)
        .options(joinedload(OptionItem.option_group).joinedload(OptionGroup.items))
        .where(OptionItem.id.in_(item_ids), OptionItem.is_deleted == False)
    )
    result = await db.execute(stmt)
    return list(result.unique().scalars().all())
