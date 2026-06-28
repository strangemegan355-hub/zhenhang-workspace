from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import aftersales_repository as repo
from app.schemas.aftersales import (
    AfterSalesServiceRequestCreate,
    AfterSalesServiceRequestRead,
    AfterSalesServiceRequestUpdate,
)
from app.schemas.common import PageResponse


def _to_read(obj) -> AfterSalesServiceRequestRead:
    return AfterSalesServiceRequestRead(
        id=obj.id,
        request_no=obj.request_no,
        title=obj.title,
        customer_id=obj.customer_id,
        customer_name=obj.customer.name if obj.customer else None,
        equipment_unit_id=obj.equipment_unit_id,
        equipment_serial=obj.equipment_unit.serial_number if obj.equipment_unit else None,
        status=obj.status,
        priority=obj.priority,
        description=obj.description,
        assigned_to=obj.assigned_to,
        assignee_name=obj.assignee.username if obj.assignee else None,
        scheduled_date=obj.scheduled_date,
        completed_date=obj.completed_date,
        resolution=obj.resolution,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        created_by=obj.created_by,
    )


async def list_requests(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    customer_id: UUID | None = None,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: UUID | None = None,
) -> PageResponse:
    total, items = await repo.list_requests(
        db, page=page, page_size=page_size,
        customer_id=customer_id, status=status,
        priority=priority, assigned_to=assigned_to,
    )
    return PageResponse(
        total=total, page=page, page_size=page_size,
        items=[_to_read(item) for item in items],
    )


async def get_request(db: AsyncSession, request_id: UUID) -> AfterSalesServiceRequestRead:
    obj = await repo.get_request(db, request_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")
    return _to_read(obj)


async def create_request(
    db: AsyncSession,
    payload: AfterSalesServiceRequestCreate,
    current_user: User,
) -> AfterSalesServiceRequestRead:
    obj = await repo.create_request(db, {
        "request_no": await repo.generate_request_no(db),
        "title": payload.title.strip(),
        "customer_id": payload.customer_id,
        "equipment_unit_id": payload.equipment_unit_id,
        "status": "draft",
        "priority": payload.priority or "medium",
        "description": payload.description.strip() if payload.description else None,
        "assigned_to": payload.assigned_to,
        "scheduled_date": payload.scheduled_date,
        "created_by": current_user.id,
    })
    return _to_read(obj)


async def update_request(
    db: AsyncSession,
    request_id: UUID,
    payload: AfterSalesServiceRequestUpdate,
) -> AfterSalesServiceRequestRead:
    obj = await repo.get_request(db, request_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")

    updates = payload.model_dump(exclude_unset=True)
    if updates.get("status") == "completed" and obj.status != "completed":
        updates["completed_date"] = date.today()
    for key, value in updates.items():
        if value is not None:
            setattr(obj, key, value)

    await repo.save_request(db, obj)
    return _to_read(obj)


async def delete_request(db: AsyncSession, request_id: UUID) -> None:
    obj = await repo.get_request(db, request_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")
    if obj.status not in ("draft", "cancelled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft or cancelled requests can be deleted")
    obj.is_deleted = True
    await repo.save_request(db, obj)
