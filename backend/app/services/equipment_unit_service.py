from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import equipment_unit_repository as repo


async def create_equipment_unit(db: AsyncSession, data: dict, current: User):
    existing = await repo.get_equipment_unit_by_serial(db, data["serial_number"])
    if existing:
        raise ValueError(f"设备序列号 {data['serial_number']} 已存在")
    return await repo.create_equipment_unit(db, data, current.id)


async def list_equipment_units(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    build_status: str | None = None,
    machine_id: UUID | None = None,
    customer_id: UUID | None = None,
):
    items, total = await repo.list_equipment_units(
        db, page, page_size, q, build_status, machine_id, customer_id
    )
    result = []
    for item in items:
        d = {
            "id": item.id,
            "serial_number": item.serial_number,
            "machine_id": item.machine_id,
            "machine_name": item.machine.name if item.machine else None,
            "machine_code": item.machine.machine_code if item.machine else None,
            "model_no": item.machine.model_no if item.machine else None,
            "build_status": item.build_status,
            "project_id": item.project_id,
            "customer_id": item.customer_id,
            "customer_name": item.customer.name if item.customer else None,
            "build_start_date": item.build_start_date,
            "ship_date": item.ship_date,
            "install_date": item.install_date,
            "acceptance_date": item.acceptance_date,
            "warranty_expiry_date": item.warranty_expiry_date,
            "remarks": item.remarks,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        result.append(d)
    return result, total


async def get_equipment_unit(db: AsyncSession, unit_id: UUID):
    unit = await repo.get_equipment_unit_by_id(db, unit_id)
    if not unit:
        raise ValueError(f"设备 {unit_id} 不存在")
    return {
        "id": unit.id,
        "serial_number": unit.serial_number,
        "machine_id": unit.machine_id,
        "machine_name": unit.machine.name if unit.machine else None,
        "machine_code": unit.machine.machine_code if unit.machine else None,
        "model_no": unit.machine.model_no if unit.machine else None,
        "build_status": unit.build_status,
        "project_id": unit.project_id,
        "customer_id": unit.customer_id,
        "customer_name": unit.customer.name if unit.customer else None,
        "build_start_date": unit.build_start_date,
        "ship_date": unit.ship_date,
        "install_date": unit.install_date,
        "acceptance_date": unit.acceptance_date,
        "warranty_expiry_date": unit.warranty_expiry_date,
        "remarks": unit.remarks,
        "created_at": unit.created_at,
        "updated_at": unit.updated_at,
    }


async def update_equipment_unit(db: AsyncSession, unit_id: UUID, data: dict):
    unit = await repo.get_equipment_unit_by_id(db, unit_id)
    if not unit:
        raise ValueError(f"设备 {unit_id} 不存在")
    if "serial_number" in data and data["serial_number"]:
        existing = await repo.get_equipment_unit_by_serial(db, data["serial_number"])
        if existing and existing.id != unit_id:
            raise ValueError(f"设备序列号 {data['serial_number']} 已被占用")
    await repo.update_equipment_unit(db, unit, data)
    return await get_equipment_unit(db, unit_id)


async def advance_build_status(db: AsyncSession, unit_id: UUID, new_status: str):
    """Advance the equipment lifecycle status with validation."""
    VALID_TRANSITIONS = {
        "in_production": ["in_stock"],
        "in_stock": ["shipped"],
        "shipped": ["installed"],
        "installed": ["running", "under_maintenance"],
        "running": ["under_maintenance", "decommissioned"],
        "under_maintenance": ["running", "decommissioned"],
        "decommissioned": [],
    }
    unit = await repo.get_equipment_unit_by_id(db, unit_id)
    if not unit:
        raise ValueError(f"设备 {unit_id} 不存在")
    if new_status not in VALID_TRANSITIONS.get(unit.build_status, []):
        raise ValueError(f"不允许从 {unit.build_status} 变更为 {new_status}")
    await repo.update_equipment_unit(db, unit, {"build_status": new_status})
    return await get_equipment_unit(db, unit_id)
