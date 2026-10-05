from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import installation_plan_repository as repo


async def list_plans(db: AsyncSession, equipment_unit_id: UUID) -> list[dict]:
    plans = await repo.list_plans(db, equipment_unit_id)
    return [_plan_to_dict(p) for p in plans]


async def get_plan(db: AsyncSession, plan_id: UUID) -> dict:
    p = await repo.get_plan_by_id(db, plan_id)
    if not p:
        raise ValueError(f"安装计划 {plan_id} 不存在")
    return _plan_to_dict(p)


async def create_plan(db: AsyncSession, data: dict, current) -> dict:
    items = data.pop("install_items", [])
    data["install_items"] = [i.model_dump(by_alias=True) if hasattr(i, "model_dump") else i for i in items]
    comm = data.pop("commissioning_items", [])
    data["commissioning_items"] = [i.model_dump(by_alias=True) if hasattr(i, "model_dump") else i for i in comm]
    p = await repo.create_plan(db, data, current.id)
    await db.refresh(p)
    return _plan_to_dict(p)


async def update_plan(db: AsyncSession, plan_id: UUID, data: dict) -> dict:
    p = await repo.get_plan_by_id(db, plan_id)
    if not p:
        raise ValueError(f"安装计划 {plan_id} 不存在")
    for field in ["install_items", "commissioning_items"]:
        if field in data and data[field] is not None:
            items = data[field]
            data = {**data, field: [i.model_dump(by_alias=True) if hasattr(i, "model_dump") else i for i in items]}
    # Auto-set dates on status change
    if "status" in data:
        now = datetime.now(timezone.utc)
        if data["status"] == "in_progress" and p.actual_start_date is None:
            data["actual_start_date"] = now
        elif data["status"] == "completed" and p.actual_end_date is None:
            data["actual_end_date"] = now
    # Auto-set customer_accepted_date
    if data.get("customer_accepted") and p.customer_accepted_date is None:
        data["customer_accepted_date"] = datetime.now(timezone.utc)
    await repo.update_plan(db, p, data)
    return _plan_to_dict(p)


async def delete_plan(db: AsyncSession, plan_id: UUID) -> None:
    p = await repo.get_plan_by_id(db, plan_id)
    if not p:
        raise ValueError(f"安装计划 {plan_id} 不存在")
    await repo.delete_plan(db, p)


def _plan_to_dict(p) -> dict:
    return {
        "id": p.id,
        "equipment_unit_id": p.equipment_unit_id,
        "planned_start_date": p.planned_start_date,
        "planned_end_date": p.planned_end_date,
        "actual_start_date": p.actual_start_date,
        "actual_end_date": p.actual_end_date,
        "status": p.status,
        "install_items": p.install_items or [],
        "commissioning_items": p.commissioning_items or [],
        "customer_representative": p.customer_representative,
        "customer_accepted": p.customer_accepted,
        "customer_accepted_date": p.customer_accepted_date,
        "remarks": p.remarks,
        "created_at": p.created_at,
    }
