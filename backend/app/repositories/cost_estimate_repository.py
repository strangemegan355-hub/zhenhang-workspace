from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cost_estimate import (
    CostEstimate,
    CostEstimateMachineLine,
    CostEstimateMaterialLine,
    CostEstimateProcessLine,
)
from app.repositories.common_repository import paginate_query


async def count_estimate_no_prefix(db: AsyncSession, prefix: str) -> int:
    stmt = select(func.count()).select_from(CostEstimate).where(
        CostEstimate.estimate_no.like(f"{prefix}%"),
        CostEstimate.is_deleted.is_(False),
    )
    return int((await db.execute(stmt)).scalar_one())


async def create_cost_estimate(db: AsyncSession, data: dict, *, autocommit: bool = True) -> CostEstimate:
    lines = {
        "material_lines": data.pop("material_lines", []),
        "machine_lines": data.pop("machine_lines", []),
        "process_lines": data.pop("process_lines", []),
    }
    obj = CostEstimate(**data)
    db.add(obj)
    await db.flush()
    await _replace_lines(db, obj, lines)
    if autocommit:
        await db.commit()
    return await get_cost_estimate(db, obj.id)


async def list_cost_estimates(
    db: AsyncSession, page: int, page_size: int, q: str | None, predicate=None
):
    extra_filters = (predicate,) if predicate is not None else ()
    return await paginate_query(
        db,
        CostEstimate,
        page,
        page_size,
        q,
        [CostEstimate.estimate_no, CostEstimate.product_name, CostEstimate.drawing_no],
        extra_filters=extra_filters,
    )


async def get_cost_estimate(
    db: AsyncSession, object_id: UUID, predicate=None
) -> CostEstimate | None:
    stmt = (
        select(CostEstimate)
        .where(CostEstimate.id == object_id, CostEstimate.is_deleted.is_(False))
        .options(
            selectinload(CostEstimate.material_lines),
            selectinload(CostEstimate.machine_lines),
            selectinload(CostEstimate.process_lines),
            selectinload(CostEstimate.customer),
        )
    )
    if predicate is not None:
        stmt = stmt.where(predicate)
    return (await db.execute(stmt)).scalar_one_or_none()


async def update_cost_estimate(db: AsyncSession, obj: CostEstimate, data: dict, *, autocommit: bool = True) -> CostEstimate:
    material_lines = data.pop("material_lines", None)
    machine_lines = data.pop("machine_lines", None)
    process_lines = data.pop("process_lines", None)
    for key, value in data.items():
        setattr(obj, key, value)
    await db.flush()
    if material_lines is not None or machine_lines is not None or process_lines is not None:
        await _replace_lines(
            db,
            obj,
            {
                "material_lines": material_lines if material_lines is not None else [],
                "machine_lines": machine_lines if machine_lines is not None else [],
                "process_lines": process_lines if process_lines is not None else [],
            },
            replace_all=material_lines is not None or machine_lines is not None or process_lines is not None,
        )
    if autocommit:
        await db.commit()
    return await get_cost_estimate(db, obj.id)


async def soft_delete_cost_estimate(db: AsyncSession, obj: CostEstimate, *, autocommit: bool = True) -> CostEstimate:
    obj.is_deleted = True
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def _replace_lines(db: AsyncSession, obj: CostEstimate, lines: dict, *, replace_all: bool = True) -> None:
    if replace_all:
        for existing in list(obj.material_lines):
            existing.is_deleted = True
        for existing in list(obj.machine_lines):
            existing.is_deleted = True
        for existing in list(obj.process_lines):
            existing.is_deleted = True
        await db.flush()

    for idx, row in enumerate(lines.get("material_lines", [])):
        db.add(
            CostEstimateMaterialLine(
                cost_estimate_id=obj.id,
                material_id=row.get("material_id"),
                name=row["name"],
                spec=row.get("spec"),
                qty=row["qty"],
                unit=row.get("unit") or "EA",
                unit_price=row.get("unit_price") or Decimal("0"),
                line_total=row.get("line_total") or Decimal("0"),
                sort_order=row.get("sort_order", idx),
            )
        )
    for idx, row in enumerate(lines.get("machine_lines", [])):
        db.add(
            CostEstimateMachineLine(
                cost_estimate_id=obj.id,
                machine_id=row.get("machine_id"),
                name=row["name"],
                spec=row.get("spec"),
                power_kw=row.get("power_kw"),
                unit_price=row.get("unit_price") or Decimal("0"),
                qty=row.get("qty") or Decimal("1"),
                line_total=row.get("line_total") or Decimal("0"),
                sort_order=row.get("sort_order", idx),
            )
        )
    for idx, row in enumerate(lines.get("process_lines", [])):
        db.add(
            CostEstimateProcessLine(
                cost_estimate_id=obj.id,
                process_name=row["process_name"],
                equipment=row.get("equipment"),
                hours=row.get("hours") or Decimal("0"),
                rate=row.get("rate") or Decimal("0"),
                line_total=row.get("line_total") or Decimal("0"),
                sort_order=row.get("sort_order", idx),
            )
        )
    await db.flush()


async def generate_estimate_no(db: AsyncSession) -> str:
    prefix = f"CB-{date.today().strftime('%Y%m%d')}-"
    count = await count_estimate_no_prefix(db, prefix)
    return f"{prefix}{count + 1:03d}"
