from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import MachineParameter
from app.repositories.machine_repository import get_machine


def _pick_param(params: list[MachineParameter], *keys: str) -> str | None:
    key_set = {k.lower() for k in keys}
    for param in params:
        if param.param_key.lower() in key_set and param.value:
            return param.value
    return None


async def get_machine_pricing_profile(db: AsyncSession, machine_id: UUID) -> dict:
    machine = await get_machine(db, machine_id)
    if machine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")

    stmt = select(MachineParameter).where(
        MachineParameter.machine_id == machine_id,
        MachineParameter.is_deleted.is_(False),
    )
    params = list((await db.execute(stmt)).scalars().all())

    reference = _pick_param(params, "reference_price", "list_price", "price")
    return {
        "machine_id": machine.id,
        "code": machine.code,
        "name": machine.name,
        "model_no": machine.model_no,
        "spec": _pick_param(params, "spec", "规格"),
        "power_kw": _pick_param(params, "power_kw", "power", "功率"),
        "reference_price": reference,
    }
