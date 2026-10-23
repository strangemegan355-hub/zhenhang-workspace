from decimal import Decimal
from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import scope_predicate
from app.core.money import money as _money
from app.models.cost_estimate import CostEstimate
from app.models.user import User
from app.repositories import cost_estimate_repository as repo
from app.schemas.common import PageResponse
from app.schemas.common import page_response as _page
from app.schemas.cost_estimate import (
    CostEstimateCreate,
    CostEstimateListItem,
    CostEstimateMachineLineRead,
    CostEstimateMaterialLineRead,
    CostEstimatePreviewResponse,
    CostEstimateProcessLineRead,
    CostEstimateRead,
    CostEstimateUpdate,
)
from app.services.business_settings_service import get_business_settings_dict

T = TypeVar("T", bound=BaseModel)

_TWOPLACES = Decimal("0.01")


def _line_material(row: dict) -> dict:
    qty = Decimal(str(row.get("qty", 1)))
    unit_price = Decimal(str(row.get("unit_price", 0)))
    line_total = _money(qty * unit_price)
    return {**row, "qty": qty, "unit_price": unit_price, "line_total": line_total}

def _line_machine(row: dict) -> dict:
    qty = Decimal(str(row.get("qty", 1)))
    unit_price = Decimal(str(row.get("unit_price", 0)))
    line_total = _money(qty * unit_price)
    return {**row, "qty": qty, "unit_price": unit_price, "line_total": line_total}

def _line_process(row: dict) -> dict:
    hours = Decimal(str(row.get("hours", 0)))
    rate = Decimal(str(row.get("rate", 0)))
    line_total = _money(hours * rate)
    return {**row, "hours": hours, "rate": rate, "line_total": line_total}

def _resolve_rates(payload: dict, defaults: dict) -> dict:
    return {
        "scrap_rate": Decimal(
            str(payload.get("scrap_rate") if payload.get("scrap_rate") is not None else defaults.get("default_scrap_rate", 0))
        ),
        "overhead_rate": Decimal(
            str(
                payload.get("overhead_rate")
                if payload.get("overhead_rate") is not None
                else defaults.get("default_overhead_rate", 0)
            )
        ),
        "profit_rate": Decimal(
            str(payload.get("profit_rate") if payload.get("profit_rate") is not None else defaults.get("default_profit_rate", 20))
        ),
        "tax_rate": Decimal(
            str(payload.get("tax_rate") if payload.get("tax_rate") is not None else defaults.get("default_tax_rate", 13))
        ),
    }

def calculate_cost_estimate(payload: dict, *, defaults: dict | None = None) -> dict:
    defaults = defaults or {}
    material_lines = [_line_material(dict(row)) for row in payload.get("material_lines", [])]
    machine_lines = [_line_machine(dict(row)) for row in payload.get("machine_lines", [])]
    process_lines = [_line_process(dict(row)) for row in payload.get("process_lines", [])]

    material_cost = _money(sum((row["line_total"] for row in material_lines), Decimal("0")))
    machine_cost = _money(sum((row["line_total"] for row in machine_lines), Decimal("0")))
    labor_cost = _money(sum((row["line_total"] for row in process_lines), Decimal("0")))
    outsource_cost = _money(Decimal(str(payload.get("outsource_cost", 0))))
    logistics_cost = _money(Decimal(str(payload.get("logistics_cost", 0))))
    other_cost = _money(outsource_cost + logistics_cost)
    base_cost = _money(material_cost + machine_cost + labor_cost + other_cost)

    rates = _resolve_rates(payload, defaults)
    scrap_cost = _money(base_cost * rates["scrap_rate"] / Decimal("100"))
    overhead_cost = _money((base_cost + scrap_cost) * rates["overhead_rate"] / Decimal("100"))
    total_cost = _money(base_cost + scrap_cost + overhead_cost)
    profit_amount = _money(total_cost * rates["profit_rate"] / Decimal("100"))
    before_tax = _money(total_cost + profit_amount)
    tax_amount = _money(before_tax * rates["tax_rate"] / Decimal("100"))
    final_total = _money(before_tax + tax_amount)

    qty = Decimal(str(payload.get("qty", 1)))
    unit_final = _money(final_total / qty if qty > 0 else Decimal("0"))

    return {
        "material_cost": material_cost,
        "machine_cost": machine_cost,
        "labor_cost": labor_cost,
        "other_cost": other_cost,
        "base_cost": base_cost,
        "scrap_cost": scrap_cost,
        "overhead_cost": overhead_cost,
        "total_cost": total_cost,
        "profit_amount": profit_amount,
        "before_tax": before_tax,
        "tax_amount": tax_amount,
        "final_total": final_total,
        "unit_final": unit_final,
        **rates,
        "material_lines": material_lines,
        "machine_lines": machine_lines,
        "process_lines": process_lines,
    }

def _to_read(obj) -> CostEstimateRead:
    base = CostEstimateRead.model_validate(obj)
    return base.model_copy(
        update={
            "material_lines": [
                CostEstimateMaterialLineRead.model_validate(line)
                for line in obj.material_lines
                if not line.is_deleted
            ],
            "machine_lines": [
                CostEstimateMachineLineRead.model_validate(line)
                for line in obj.machine_lines
                if not line.is_deleted
            ],
            "process_lines": [
                CostEstimateProcessLineRead.model_validate(line)
                for line in obj.process_lines
                if not line.is_deleted
            ],
        }
    )

async def preview_cost_estimate(db: AsyncSession, payload: CostEstimateCreate) -> CostEstimatePreviewResponse:
    defaults = await get_business_settings_dict(db)
    calc = calculate_cost_estimate(payload.model_dump(), defaults=defaults)
    return CostEstimatePreviewResponse.model_validate(calc)

async def create_cost_estimate(db: AsyncSession, payload: CostEstimateCreate, current_user: User) -> CostEstimateRead:
    defaults = await get_business_settings_dict(db)
    data = payload.model_dump()
    calc = calculate_cost_estimate(data, defaults=defaults)
    estimate_no = await repo.generate_estimate_no(db)
    save_payload = {
        **data,
        "estimate_no": estimate_no,
        "status": "draft",
        "created_by": current_user.id,
        "material_cost": calc["material_cost"],
        "machine_cost": calc["machine_cost"],
        "labor_cost": calc["labor_cost"],
        "other_cost": calc["other_cost"],
        "base_cost": calc["base_cost"],
        "scrap_cost": calc["scrap_cost"],
        "overhead_cost": calc["overhead_cost"],
        "total_cost": calc["total_cost"],
        "profit_amount": calc["profit_amount"],
        "before_tax": calc["before_tax"],
        "tax_amount": calc["tax_amount"],
        "final_total": calc["final_total"],
        "unit_final": calc["unit_final"],
        "scrap_rate": calc["scrap_rate"],
        "overhead_rate": calc["overhead_rate"],
        "profit_rate": calc["profit_rate"],
        "tax_rate": calc["tax_rate"],
        "material_lines": calc["material_lines"],
        "machine_lines": calc["machine_lines"],
        "process_lines": calc["process_lines"],
    }
    obj = await repo.create_cost_estimate(db, save_payload)
    return _to_read(obj)

async def list_cost_estimates(
    db: AsyncSession, page: int, page_size: int, q: str | None, current_user: User
) -> PageResponse:
    total, items = await repo.list_cost_estimates(
        db, page, page_size, q, predicate=scope_predicate(CostEstimate, current_user)
    )
    return _page(total, page, page_size, items, CostEstimateListItem)

async def get_cost_estimate_or_404(
    db: AsyncSession, object_id: UUID, current_user: User
) -> CostEstimateRead:
    obj = await repo.get_cost_estimate(
        db, object_id, predicate=scope_predicate(CostEstimate, current_user)
    )
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost estimate not found")
    return _to_read(obj)

async def update_cost_estimate(
    db: AsyncSession, object_id: UUID, payload: CostEstimateUpdate, current_user: User
) -> CostEstimateRead:
    obj = await repo.get_cost_estimate(
        db, object_id, predicate=scope_predicate(CostEstimate, current_user)
    )
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost estimate not found")

    updates = payload.model_dump(exclude_unset=True)
    merged = {
        "product_name": obj.product_name,
        "product_spec": obj.product_spec,
        "power_kw": obj.power_kw,
        "customer_id": obj.customer_id,
        "drawing_no": obj.drawing_no,
        "qty": obj.qty,
        "delivery_note": obj.delivery_note,
        "remark": obj.remark,
        "outsource_cost": obj.outsource_cost,
        "logistics_cost": obj.logistics_cost,
        "scrap_rate": float(obj.scrap_rate),
        "overhead_rate": float(obj.overhead_rate),
        "profit_rate": float(obj.profit_rate),
        "tax_rate": float(obj.tax_rate),
        "material_lines": [
            {
                "material_id": line.material_id,
                "name": line.name,
                "spec": line.spec,
                "qty": line.qty,
                "unit": line.unit,
                "unit_price": line.unit_price,
                "sort_order": line.sort_order,
            }
            for line in obj.material_lines
            if not line.is_deleted
        ],
        "machine_lines": [
            {
                "machine_id": line.machine_id,
                "name": line.name,
                "spec": line.spec,
                "power_kw": line.power_kw,
                "unit_price": line.unit_price,
                "qty": line.qty,
                "sort_order": line.sort_order,
            }
            for line in obj.machine_lines
            if not line.is_deleted
        ],
        "process_lines": [
            {
                "process_name": line.process_name,
                "equipment": line.equipment,
                "hours": line.hours,
                "rate": line.rate,
                "sort_order": line.sort_order,
            }
            for line in obj.process_lines
            if not line.is_deleted
        ],
    }
    merged.update(updates)

    defaults = await get_business_settings_dict(db)
    calc = calculate_cost_estimate(merged, defaults=defaults)
    save_payload = {
        **{k: v for k, v in updates.items() if k not in {"material_lines", "machine_lines", "process_lines"}},
        "material_cost": calc["material_cost"],
        "machine_cost": calc["machine_cost"],
        "labor_cost": calc["labor_cost"],
        "other_cost": calc["other_cost"],
        "base_cost": calc["base_cost"],
        "scrap_cost": calc["scrap_cost"],
        "overhead_cost": calc["overhead_cost"],
        "total_cost": calc["total_cost"],
        "profit_amount": calc["profit_amount"],
        "before_tax": calc["before_tax"],
        "tax_amount": calc["tax_amount"],
        "final_total": calc["final_total"],
        "unit_final": calc["unit_final"],
        "scrap_rate": calc["scrap_rate"],
        "overhead_rate": calc["overhead_rate"],
        "profit_rate": calc["profit_rate"],
        "tax_rate": calc["tax_rate"],
    }
    if "material_lines" in updates or "machine_lines" in updates or "process_lines" in updates:
        save_payload["material_lines"] = calc["material_lines"]
        save_payload["machine_lines"] = calc["machine_lines"]
        save_payload["process_lines"] = calc["process_lines"]

    updated = await repo.update_cost_estimate(db, obj, save_payload)
    return _to_read(updated)

async def delete_cost_estimate(
    db: AsyncSession, object_id: UUID, current_user: User
) -> CostEstimateRead:
    obj = await repo.get_cost_estimate(
        db, object_id, predicate=scope_predicate(CostEstimate, current_user)
    )
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost estimate not found")
    deleted = await repo.soft_delete_cost_estimate(db, obj)
    return _to_read(deleted)
