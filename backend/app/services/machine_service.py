from datetime import date
from typing import TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UniqueViolationException
from app.models.user import User
from app.repositories import machine_repository as repo
from app.schemas.common import PageResponse
from app.schemas.common import page_response as _page
from app.schemas.machine import (
    MachineBomItemRead,
    MachineBomRead,
    MachineCategoryRead,
    MachineImageRead,
    MachineParameterRead,
    MachineRead,
)
from app.services.audit_service import write_audit_log
from app.services.workflow_service import get_next_state_code

T = TypeVar("T", bound=BaseModel)

async def _get_or_404(getter, db: AsyncSession, object_id, label: str):
    obj = await getter(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj

async def create_machine_category(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    return await repo.create_machine_category(db, payload)

async def list_machine_categories(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, items = await repo.list_machine_categories(db, page, page_size, q)
    return _page(total, page, page_size, items, MachineCategoryRead)

async def update_machine_category(db: AsyncSession, object_id, payload: dict):
    obj = await _get_or_404(repo.get_machine_category, db, object_id, "Machine category")
    return await repo.update_machine_category(db, obj, payload)

async def delete_machine_category(db: AsyncSession, object_id):
    obj = await _get_or_404(repo.get_machine_category, db, object_id, "Machine category")
    return await repo.soft_delete_machine_category(db, obj)

async def create_machine(db: AsyncSession, payload: dict, current_user: User):
    if await repo.exists_machine_name(db, payload["name"]):
        raise UniqueViolationException("machine.name", payload["name"])
    payload["created_by"] = current_user.id
    payload["machine_code"] = await _generate_machine_code(db, payload.get("code", "MACHINE"))
    return await repo.create_machine(db, payload)

async def list_machines(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, items = await repo.list_machines(db, page, page_size, q)
    return _page(total, page, page_size, items, MachineRead)

async def update_machine(db: AsyncSession, object_id, payload: dict):
    obj = await _get_or_404(repo.get_machine, db, object_id, "Machine")
    if "machine_code" in payload and payload["machine_code"]:
        if await repo.exists_machine_code(db, payload["machine_code"], exclude_id=obj.id):
            raise UniqueViolationException("machine.machine_code", payload["machine_code"])
    if "name" in payload and payload["name"]:
        if await repo.exists_machine_name(db, payload["name"], exclude_id=obj.id):
            raise UniqueViolationException("machine.name", payload["name"])
    return await repo.update_machine(db, obj, payload)

async def delete_machine(db: AsyncSession, object_id):
    obj = await _get_or_404(repo.get_machine, db, object_id, "Machine")
    return await repo.soft_delete_machine(db, obj)

async def create_machine_parameter(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    return await repo.create_machine_parameter(db, payload)

async def list_machine_parameters(
    db: AsyncSession, page: int, page_size: int, q: str | None, *, machine_id=None
) -> PageResponse:
    total, items = await repo.list_machine_parameters(db, page, page_size, q, machine_id=machine_id)
    return _page(total, page, page_size, items, MachineParameterRead)

async def update_machine_parameter(db: AsyncSession, object_id, payload: dict):
    obj = await _get_or_404(repo.get_machine_parameter, db, object_id, "Machine parameter")
    return await repo.update_machine_parameter(db, obj, payload)

async def delete_machine_parameter(db: AsyncSession, object_id):
    obj = await _get_or_404(repo.get_machine_parameter, db, object_id, "Machine parameter")
    return await repo.soft_delete_machine_parameter(db, obj)

async def create_machine_image(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    return await repo.create_machine_image(db, payload)

async def list_machine_images(
    db: AsyncSession, page: int, page_size: int, q: str | None, *, machine_id=None
) -> PageResponse:
    total, items = await repo.list_machine_images(db, page, page_size, q, machine_id=machine_id)
    return _page(total, page, page_size, items, MachineImageRead)

async def update_machine_image(db: AsyncSession, object_id, payload: dict):
    obj = await _get_or_404(repo.get_machine_image, db, object_id, "Machine image")
    return await repo.update_machine_image(db, obj, payload)

async def delete_machine_image(db: AsyncSession, object_id):
    obj = await _get_or_404(repo.get_machine_image, db, object_id, "Machine image")
    return await repo.soft_delete_machine_image(db, obj)

async def create_machine_bom(db: AsyncSession, payload: dict, current_user: User):
    if await repo.exists_bom_version(db, payload["machine_id"], payload["version"]):
        raise UniqueViolationException("machine_bom.version", payload["version"])
    payload["created_by"] = current_user.id
    payload["effective_date"] = payload.get("effective_date") or date.today()
    payload["total_cost"] = 0
    created = await repo.create_machine_bom(db, payload)
    if created.is_active:
        await repo.deactivate_other_boms(db, created.machine_id, created.id)
        await db.commit()
        await db.refresh(created)
    return created

async def get_machine_bom(db: AsyncSession, bom_id):
    return await _get_or_404(repo.get_machine_bom, db, bom_id, "Machine BOM")

async def list_machine_boms(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, items = await repo.list_machine_boms(db, page, page_size, q)
    return _page(total, page, page_size, items, MachineBomRead)

async def update_machine_bom(db: AsyncSession, object_id, payload: dict):
    obj = await _get_or_404(repo.get_machine_bom, db, object_id, "Machine BOM")
    if "version" in payload and payload["version"]:
        if await repo.exists_bom_version(db, obj.machine_id, payload["version"], exclude_id=obj.id):
            raise UniqueViolationException("machine_bom.version", payload["version"])
    if payload.get("is_active") is True:
        await repo.deactivate_other_boms(db, obj.machine_id, obj.id)
    if payload.get("status") and payload["status"] != obj.status:
        payload["status"] = await get_next_state_code(
            db,
            entity_type="machine_bom",
            current_state_code=obj.status,
            action_code=payload["status"],
        )
    updated = await repo.update_machine_bom(db, obj, payload)
    await repo.recalculate_bom_total_cost(db, updated.id)
    await db.commit()
    await db.refresh(updated)
    return updated

async def delete_machine_bom(db: AsyncSession, object_id):
    obj = await _get_or_404(repo.get_machine_bom, db, object_id, "Machine BOM")
    deleted = await repo.soft_delete_machine_bom(db, obj)
    await repo.recalculate_bom_total_cost(db, obj.id)
    await db.commit()
    return deleted

async def create_machine_bom_item(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    obj = await repo.create_machine_bom_item(db, payload)
    await repo.recalculate_bom_total_cost(db, obj.bom_id)
    await write_audit_log(
        db,
        module="bom",
        action="create_item",
        resource_type="machine_bom_item",
        resource_id=obj.id,
        created_by=current_user.id,
        payload=payload,
    )
    await db.commit()
    await db.refresh(obj)
    return obj

async def list_machine_bom_items(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    *,
    bom_id=None,
) -> PageResponse:
    total, items = await repo.list_machine_bom_items(db, page, page_size, q, bom_id=bom_id)
    return _page(total, page, page_size, items, MachineBomItemRead)

async def update_machine_bom_item(db: AsyncSession, object_id, payload: dict):
    obj = await _get_or_404(repo.get_machine_bom_item, db, object_id, "Machine BOM item")
    updated = await repo.update_machine_bom_item(db, obj, payload)
    await repo.recalculate_bom_total_cost(db, updated.bom_id)
    await db.commit()
    await db.refresh(updated)
    return updated

async def delete_machine_bom_item(db: AsyncSession, object_id):
    obj = await _get_or_404(repo.get_machine_bom_item, db, object_id, "Machine BOM item")
    deleted = await repo.soft_delete_machine_bom_item(db, obj)
    await repo.recalculate_bom_total_cost(db, obj.bom_id)
    await db.commit()
    return deleted

async def create_bom_items_batch(db: AsyncSession, items: list[dict], current_user: User):
    created = []
    for item in items:
        item["created_by"] = current_user.id
        created.append(await repo.create_machine_bom_item(db, item, autocommit=False))
    affected_bom_ids = sorted({row.bom_id for row in created})
    for bom_id in affected_bom_ids:
        await repo.recalculate_bom_total_cost(db, bom_id)
    await write_audit_log(
        db,
        module="bom",
        action="batch_create_items",
        resource_type="machine_bom_item",
        resource_id=None,
        created_by=current_user.id,
        payload={"count": len(created)},
    )
    await db.commit()
    for row in created:
        await db.refresh(row)
    return created

async def delete_machine_boms_batch(db: AsyncSession, ids: list, current_user: User):
    boms = await repo.get_machine_boms_by_ids(db, ids)
    for bom in boms:
        await repo.soft_delete_machine_bom(db, bom, autocommit=False)
    await write_audit_log(
        db,
        module="bom",
        action="batch_delete",
        resource_type="machine_bom",
        resource_id=None,
        created_by=current_user.id,
        payload={"ids": [str(i) for i in ids]},
    )
    await db.commit()
    return {"deleted_count": len(boms)}

async def transition_bom_status(db: AsyncSession, bom_id, action_code: str, current_user: User):
    bom = await _get_or_404(repo.get_machine_bom, db, bom_id, "Machine BOM")
    next_code = await get_next_state_code(
        db,
        entity_type="machine_bom",
        current_state_code=bom.status,
        action_code=action_code,
    )
    updated = await repo.update_machine_bom(db, bom, {"status": next_code}, autocommit=False)
    await write_audit_log(
        db,
        module="workflow",
        action="transition",
        resource_type="machine_bom",
        resource_id=bom.id,
        created_by=current_user.id,
        detail=f"{bom.status} -> {next_code}",
        payload={"action_code": action_code},
        autocommit=False,
    )
    await db.commit()
    await db.refresh(updated)
    return updated

async def _generate_machine_code(db: AsyncSession, base_code: str) -> str:
    today = date.today().strftime("%Y%m%d")
    prefix = f"{base_code[:4].upper()}-{today}-"
    seq = await repo.count_machine_code_prefix(db, prefix) + 1
    return f"{prefix}{seq:04d}"
