from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import acceptance_repository as repo


# ── Templates ──

async def list_templates(db: AsyncSession, machine_id: UUID | None = None) -> list[dict]:
    templates = await repo.list_templates(db, machine_id)
    return [_template_to_dict(t) for t in templates]


async def get_template(db: AsyncSession, template_id: UUID) -> dict:
    t = await repo.get_template_by_id(db, template_id)
    if not t:
        raise ValueError(f"验收模板 {template_id} 不存在")
    return _template_to_dict(t)


async def create_template(db: AsyncSession, data: dict, current) -> dict:
    items = data.pop("items", [])
    data["items"] = [i.model_dump(by_alias=True) if hasattr(i, "model_dump") else i for i in items]
    t = await repo.create_template(db, data, current.id)
    await db.refresh(t)
    return _template_to_dict(t)


async def update_template(db: AsyncSession, template_id: UUID, data: dict) -> dict:
    t = await repo.get_template_by_id(db, template_id)
    if not t:
        raise ValueError(f"验收模板 {template_id} 不存在")
    if "items" in data and data["items"] is not None:
        items = data["items"]
        data = {**data, "items": [i.model_dump(by_alias=True) if hasattr(i, "model_dump") else i for i in items]}
    await repo.update_template(db, t, data)
    return _template_to_dict(t)


async def delete_template(db: AsyncSession, template_id: UUID) -> None:
    t = await repo.get_template_by_id(db, template_id)
    if not t:
        raise ValueError(f"验收模板 {template_id} 不存在")
    await repo.delete_template(db, t)


# ── Records ──

async def list_records(db: AsyncSession, equipment_unit_id: UUID) -> list[dict]:
    records = await repo.list_records(db, equipment_unit_id)
    return [_record_to_dict(r) for r in records]


async def get_record(db: AsyncSession, record_id: UUID) -> dict:
    r = await repo.get_record_by_id(db, record_id)
    if not r:
        raise ValueError(f"验收记录 {record_id} 不存在")
    return _record_to_dict(r)


async def create_record(db: AsyncSession, data: dict, current) -> dict:
    items = data.pop("items", [])
    data["items"] = [i.model_dump(by_alias=True) if hasattr(i, "model_dump") else i for i in items]
    # Auto-generate record_no
    template = await repo.get_template_by_id(db, data["template_id"])
    if not template:
        raise ValueError(f"验收模板 {data['template_id']} 不存在")
    prefix = template.template_type.upper()
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    # Count existing records today for sequential number
    existing = await repo.list_records(db, data["equipment_unit_id"])
    today_count = sum(1 for r in existing if r.record_no and r.record_no.startswith(f"{prefix}-{date_str}"))
    data["record_no"] = f"{prefix}-{date_str}-{today_count + 1:04d}"
    r = await repo.create_record(db, data, current.id)
    await db.refresh(r)
    r = await repo.get_record_by_id(db, r.id)
    return _record_to_dict(r)


async def update_record(db: AsyncSession, record_id: UUID, data: dict) -> dict:
    r = await repo.get_record_by_id(db, record_id)
    if not r:
        raise ValueError(f"验收记录 {record_id} 不存在")
    if "items" in data and data["items"] is not None:
        items = data["items"]
        data = {**data, "items": [i.model_dump(by_alias=True) if hasattr(i, "model_dump") else i for i in items]}
    await repo.update_record(db, r, data)
    r = await repo.get_record_by_id(db, record_id)
    return _record_to_dict(r)


async def delete_record(db: AsyncSession, record_id: UUID) -> None:
    r = await repo.get_record_by_id(db, record_id)
    if not r:
        raise ValueError(f"验收记录 {record_id} 不存在")
    await repo.delete_record(db, r)


# ── Punch items ──

async def create_punch_item(db: AsyncSession, record_id: UUID, data: dict, current) -> dict:
    r = await repo.get_record_by_id(db, record_id)
    if not r:
        raise ValueError(f"验收记录 {record_id} 不存在")
    p = await repo.create_punch_item(db, record_id, data, current.id)
    return _punch_item_to_dict(p)


async def update_punch_item(db: AsyncSession, item_id: UUID, data: dict) -> dict:
    p = await repo.get_punch_item_by_id(db, item_id)
    if not p:
        raise ValueError(f"整改项 {item_id} 不存在")
    await repo.update_punch_item(db, p, data)
    return _punch_item_to_dict(p)


async def delete_punch_item(db: AsyncSession, item_id: UUID) -> None:
    p = await repo.get_punch_item_by_id(db, item_id)
    if not p:
        raise ValueError(f"整改项 {item_id} 不存在")
    await repo.delete_punch_item(db, p)


# ── Serializers ──

def _template_to_dict(t) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "template_type": t.template_type,
        "machine_id": t.machine_id,
        "items": t.items or [],
        "created_at": t.created_at,
    }


def _record_to_dict(r) -> dict:
    return {
        "id": r.id,
        "template_id": r.template_id,
        "equipment_unit_id": r.equipment_unit_id,
        "record_no": r.record_no,
        "test_date": r.test_date,
        "inspector_name": r.inspector_name,
        "status": r.status,
        "items": r.items or [],
        "overall_result": r.overall_result,
        "remarks": r.remarks,
        "created_at": r.created_at,
        "punch_items": [_punch_item_to_dict(p) for p in (r.punch_items or [])],
    }


def _punch_item_to_dict(p) -> dict:
    return {
        "id": p.id,
        "record_id": p.record_id,
        "description": p.description,
        "severity": p.severity,
        "status": p.status,
        "resolved_at": p.resolved_at,
        "resolution": p.resolution,
        "created_at": p.created_at,
    }
