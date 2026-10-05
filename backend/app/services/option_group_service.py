from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import option_group_repository as repo


async def list_option_groups(db: AsyncSession, machine_id: UUID) -> list[dict]:
    groups = await repo.list_option_groups(db, machine_id)
    return [_group_to_dict(g) for g in groups]


async def create_option_group(db: AsyncSession, machine_id: UUID, data: dict, current) -> dict:
    g = await repo.create_option_group(db, machine_id, data, current.id)
    await db.refresh(g)
    g = await repo.get_option_group_by_id(db, g.id)
    return _group_to_dict(g)


async def update_option_group(db: AsyncSession, group_id: UUID, data: dict) -> dict:
    group = await repo.get_option_group_by_id(db, group_id)
    if not group:
        raise ValueError(f"选配组 {group_id} 不存在")
    await repo.update_option_group(db, group, data)
    group = await repo.get_option_group_by_id(db, group_id)
    return _group_to_dict(group)


async def delete_option_group(db: AsyncSession, group_id: UUID) -> None:
    group = await repo.get_option_group_by_id(db, group_id)
    if not group:
        raise ValueError(f"选配组 {group_id} 不存在")
    await repo.delete_option_group(db, group)


async def create_option_item(db: AsyncSession, group_id: UUID, data: dict, current) -> dict:
    group = await repo.get_option_group_by_id(db, group_id)
    if not group:
        raise ValueError(f"选配组 {group_id} 不存在")
    item = await repo.create_option_item(db, group_id, data, current.id)
    return _item_to_dict(item)


async def update_option_item(db: AsyncSession, item_id: UUID, data: dict) -> dict:
    item = await repo.get_option_item_by_id(db, item_id)
    if not item:
        raise ValueError(f"选项 {item_id} 不存在")
    await repo.update_option_item(db, item, data)
    return _item_to_dict(item)


async def delete_option_item(db: AsyncSession, item_id: UUID) -> None:
    item = await repo.get_option_item_by_id(db, item_id)
    if not item:
        raise ValueError(f"选项 {item_id} 不存在")
    await repo.delete_option_item(db, item)


async def get_machine_options(db: AsyncSession, machine_id: UUID) -> list[dict]:
    """Flat option groups with items for quote selection panel."""
    groups = await repo.list_option_groups(db, machine_id)
    return [_group_to_dict(g) for g in groups]


async def get_option_items_by_ids(db: AsyncSession, item_ids: list[UUID]) -> list:
    return await repo.get_option_items_by_ids(db, item_ids)


def _group_to_dict(g) -> dict:
    return {
        "id": g.id,
        "machine_id": g.machine_id,
        "name": g.name,
        "sort_order": g.sort_order,
        "items": [_item_to_dict(i) for i in g.items],
    }


def _item_to_dict(i) -> dict:
    return {
        "id": i.id,
        "option_group_id": i.option_group_id,
        "name": i.name,
        "price_adjustment": float(i.price_adjustment),
        "sort_order": i.sort_order,
    }
