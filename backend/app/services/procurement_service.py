from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import scope_predicate
from app.models.procurement_entry import ProcurementEntry
from app.models.user import User
from app.repositories import procurement_repository as repo
from app.repositories import project_actual_cost_repository as actual_cost_repo
from app.schemas.common import PageResponse
from app.schemas.procurement_entry import (
    ProcurementEntryCreate,
    ProcurementEntryRead,
    ProcurementEntryUpdate,
    ProcurementTransferResult,
)

_STATUS_FLOW = ("planned", "ordered", "arrived")


def _to_read(obj) -> ProcurementEntryRead:
    plan_amount = (Decimal(str(obj.qty)) * Decimal(str(obj.unit_price))).quantize(Decimal("0.01"))
    return ProcurementEntryRead(
        id=obj.id,
        request_no=obj.request_no,
        project_id=obj.project_id,
        material_id=obj.material_id,
        supplier_id=obj.supplier_id,
        qty=Decimal(str(obj.qty)),
        unit_price=Decimal(str(obj.unit_price)),
        plan_amount=plan_amount,
        lead_days=obj.lead_days,
        need_date=obj.need_date,
        status=obj.status,
        transferred_to_actual=obj.transferred_to_actual,
        payable_status=getattr(obj, "payable_status", "none") or "none",
        remark=obj.remark,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        created_by=obj.created_by,
        is_deleted=obj.is_deleted,
    )


async def create_entry(db: AsyncSession, payload: ProcurementEntryCreate, current_user: User) -> ProcurementEntryRead:
    data = payload.model_dump()
    if not data.get("request_no"):
        data["request_no"] = await repo.generate_request_no(db)
    data["created_by"] = current_user.id
    obj = await repo.create_entry(db, data)
    return _to_read(obj)


async def list_entries(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    current_user: User,
    *,
    project_id: UUID | None = None,
    status: str | None = None,
) -> PageResponse:
    total, items = await repo.list_entries(
        db,
        page,
        page_size,
        q,
        project_id=project_id,
        status=status,
        predicate=scope_predicate(ProcurementEntry, current_user),
    )
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_read(i) for i in items],
    )


async def get_entry_or_404(
    db: AsyncSession, object_id: UUID, current_user: User
) -> ProcurementEntryRead:
    obj = await repo.get_entry(db, object_id, predicate=scope_predicate(ProcurementEntry, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement entry not found")
    return _to_read(obj)


async def update_entry(
    db: AsyncSession, object_id: UUID, payload: ProcurementEntryUpdate, current_user: User
) -> ProcurementEntryRead:
    obj = await repo.get_entry(db, object_id, predicate=scope_predicate(ProcurementEntry, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement entry not found")
    if obj.transferred_to_actual:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transferred entries cannot be edited")
    updated = await repo.update_entry(db, obj, payload.model_dump(exclude_unset=True))
    return _to_read(updated)


async def delete_entry(
    db: AsyncSession, object_id: UUID, current_user: User
) -> ProcurementEntryRead:
    obj = await repo.get_entry(db, object_id, predicate=scope_predicate(ProcurementEntry, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement entry not found")
    deleted = await repo.soft_delete_entry(db, obj)
    return _to_read(deleted)


async def advance_entry_status(db: AsyncSession, object_id: UUID, current_user) -> ProcurementEntryRead:
    obj = await repo.get_entry(db, object_id, predicate=scope_predicate(ProcurementEntry, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement entry not found")
    try:
        idx = _STATUS_FLOW.index(obj.status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid procurement status") from None
    if idx >= len(_STATUS_FLOW) - 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Entry already arrived")
    obj.status = _STATUS_FLOW[idx + 1]
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return _to_read(obj)


async def _transfer_one_entry(db: AsyncSession, entry, current_user: User) -> dict | None:
    if entry.status != "arrived" or entry.transferred_to_actual:
        return None
    if not entry.project_id:
        return {"entry_id": str(entry.id), "skipped": True, "reason": "missing_project"}
    amount = (Decimal(str(entry.qty)) * Decimal(str(entry.unit_price))).quantize(Decimal("0.01"))
    if amount <= 0:
        return {"entry_id": str(entry.id), "skipped": True, "reason": "zero_amount"}

    procurement_ref = str(entry.id)
    existing = await actual_cost_repo.find_by_procurement_ref(db, procurement_ref)
    if existing:
        entry.transferred_to_actual = True
        await db.flush()
        return {"entry_id": str(entry.id), "actual_cost_id": str(existing.id), "skipped": True, "reason": "already_transferred"}

    material_name = entry.material.name if entry.material else "材料"
    actual = await actual_cost_repo.create_actual_cost(
        db,
        {
            "project_id": entry.project_id,
            "cost_category": "material",
            "cost_item_code": "MAT",
            "cost_item_name": "材料与外购件",
            "amount": float(amount),
            "source": "采购到货转入",
            "supplier_id": entry.supplier_id,
            "occurred_on": entry.need_date or date.today(),
            "remark": f"采购计划转入：{material_name}；{entry.remark or '无备注'}",
            "procurement_ref": procurement_ref,
            "created_by": current_user.id,
        },
    )
    entry.transferred_to_actual = True
    await db.flush()
    return {"entry_id": str(entry.id), "actual_cost_id": str(actual.id), "amount": str(amount)}


async def transfer_arrived_to_actual_cost(db: AsyncSession, current_user: User) -> ProcurementTransferResult:
    entries = await repo.list_arrived_not_transferred(db)
    transferred: list[dict] = []
    skipped = 0
    for entry in entries:
        result = await _transfer_one_entry(db, entry, current_user)
        if result is None:
            skipped += 1
            continue
        if result.get("skipped"):
            skipped += 1
        else:
            transferred.append(result)
    await db.commit()
    return ProcurementTransferResult(
        transferred_count=len(transferred),
        skipped_count=skipped,
        items=transferred,
    )
