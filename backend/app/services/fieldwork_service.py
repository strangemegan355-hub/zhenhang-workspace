from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import scope_predicate
from app.models.fieldwork_record import FieldworkRecord
from app.models.user import User
from app.repositories import fieldwork_repository as repo
from app.schemas.common import PageResponse
from app.schemas.fieldwork_record import (
    FieldworkRecordCreate,
    FieldworkRecordRead,
    FieldworkRecordUpdate,
    FieldworkSummary,
)

_TYPE_LABELS = {"repair": "外出维修", "shortage": "缺料上报", "loading": "装车登记"}

_URGENCY_LABELS = {"normal": "正常", "urgent": "紧急", "critical": "非常紧急"}

_STATUS_LABELS = {
    "submitted": "已提交",
    "reported": "已上报",
    "acknowledged": "已确认",
    "closed": "已关闭",
}

_STATUS_FLOW = {
    "repair": ("submitted", "closed"),
    "shortage": ("reported", "acknowledged", "closed"),
    "loading": ("submitted", "closed"),
}

_INITIAL_STATUS = {
    "repair": "submitted",
    "shortage": "reported",
    "loading": "submitted",
}


def _type_label(record_type: str) -> str:
    return _TYPE_LABELS.get(record_type, record_type)


def _status_label(status: str) -> str:
    return _STATUS_LABELS.get(status, status)


def _urgency_label(urgency: str | None) -> str | None:
    if not urgency:
        return None
    return _URGENCY_LABELS.get(urgency, urgency)


def _to_read(obj) -> FieldworkRecordRead:
    return FieldworkRecordRead(
        id=obj.id,
        record_no=obj.record_no,
        record_type=obj.record_type,
        record_type_label=_type_label(obj.record_type),
        status=obj.status,
        status_label=_status_label(obj.status),
        customer_id=obj.customer_id,
        project_id=obj.project_id,
        machine_id=obj.machine_id,
        material_id=obj.material_id,
        occurred_on=obj.occurred_on,
        reporter_name=obj.reporter_name,
        headline=obj.headline,
        detail=obj.detail,
        qty=Decimal(str(obj.qty)) if obj.qty is not None else None,
        hours=Decimal(str(obj.hours)) if obj.hours is not None else None,
        repair_amount=Decimal(str(obj.repair_amount)) if obj.repair_amount is not None else None,
        receivable_entry_id=obj.receivable_entry_id,
        service_request_id=obj.service_request_id,
        service_request_title=obj.service_request.title if obj.service_request else None,
        urgency=obj.urgency,
        urgency_label=_urgency_label(obj.urgency),
        extra=obj.extra,
        remark=obj.remark,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        created_by=obj.created_by,
        is_deleted=obj.is_deleted,
    )


def _validate_create(payload: FieldworkRecordCreate) -> None:
    if payload.record_type not in _TYPE_LABELS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid fieldwork record type")
    if payload.record_type == "repair" and not payload.customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Repair record requires customer")
    if payload.record_type == "shortage":
        if not payload.machine_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shortage record requires machine")
        if not payload.material_id or payload.qty is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shortage record requires material and qty")
    if payload.record_type == "loading" and not payload.customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loading record requires customer")


async def create_record(db: AsyncSession, payload: FieldworkRecordCreate, current_user: User) -> FieldworkRecordRead:
    _validate_create(payload)
    data = payload.model_dump()
    data["record_no"] = await repo.generate_record_no(db, payload.record_type)
    data["status"] = _INITIAL_STATUS[payload.record_type]
    if not data.get("reporter_name"):
        data["reporter_name"] = current_user.full_name or current_user.username
    data["created_by"] = current_user.id
    if data.get("qty") is not None:
        data["qty"] = float(data["qty"])
    if data.get("hours") is not None:
        data["hours"] = float(data["hours"])
    if data.get("repair_amount") is not None:
        data["repair_amount"] = float(data["repair_amount"])
    obj = await repo.create_record(db, data)
    return _to_read(obj)


async def list_records(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    current_user: User,
    *,
    record_type: str | None = None,
    status: str | None = None,
    project_id: UUID | None = None,
) -> PageResponse:
    total, items = await repo.list_records(
        db,
        page,
        page_size,
        q,
        record_type=record_type,
        status=status,
        project_id=project_id,
        predicate=scope_predicate(FieldworkRecord, current_user),
    )
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_read(i) for i in items],
    )


async def get_record_or_404(
    db: AsyncSession, object_id: UUID, current_user: User
) -> FieldworkRecordRead:
    obj = await repo.get_record(db, object_id, predicate=scope_predicate(FieldworkRecord, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fieldwork record not found")
    return _to_read(obj)


async def update_record(
    db: AsyncSession, object_id: UUID, payload: FieldworkRecordUpdate, current_user: User
) -> FieldworkRecordRead:
    obj = await repo.get_record(db, object_id, predicate=scope_predicate(FieldworkRecord, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fieldwork record not found")
    data = payload.model_dump(exclude_unset=True)
    if "repair_amount" in data and obj.receivable_entry_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已生成应收，不可修改维修费用")
    if data.get("repair_amount") is not None:
        data["repair_amount"] = float(data["repair_amount"])
    updated = await repo.update_record(db, obj, data)
    return _to_read(updated)


async def delete_record(
    db: AsyncSession, object_id: UUID, current_user: User
) -> FieldworkRecordRead:
    obj = await repo.get_record(db, object_id, predicate=scope_predicate(FieldworkRecord, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fieldwork record not found")
    deleted = await repo.soft_delete_record(db, obj)
    return _to_read(deleted)


async def advance_record_status(db: AsyncSession, object_id: UUID, current_user) -> FieldworkRecordRead:
    obj = await repo.get_record(db, object_id, predicate=scope_predicate(FieldworkRecord, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fieldwork record not found")
    flow = _STATUS_FLOW.get(obj.record_type)
    if not flow:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid record type")
    try:
        idx = flow.index(obj.status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid record status") from None
    if idx >= len(flow) - 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Record already closed")
    obj.status = flow[idx + 1]
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return _to_read(obj)


async def get_summary(db: AsyncSession, current_user: User) -> FieldworkSummary:
    # The counts carry the same scope as the list: a total is a read of every row it sums.
    predicate = scope_predicate(FieldworkRecord, current_user)
    counts = await repo.count_by_type(db, predicate)
    repair = counts.get("repair", 0)
    shortage = counts.get("shortage", 0)
    loading = counts.get("loading", 0)
    return FieldworkSummary(
        total=repair + shortage + loading,
        repair=repair,
        shortage=shortage,
        loading=loading,
        open_shortages=await repo.count_open_shortages(db, predicate),
    )
