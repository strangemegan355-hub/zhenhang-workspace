from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.procurement_payable_request import ProcurementPayableRequest

# Re-export for service call sites (`ppr_repo.commit_session`); do not inline-delete.
from app.repositories.base import commit_session as commit_session


async def get_request(db: AsyncSession, request_id: UUID) -> ProcurementPayableRequest | None:
    result = await db.execute(
        select(ProcurementPayableRequest)
        .where(ProcurementPayableRequest.id == request_id, ProcurementPayableRequest.is_deleted.is_(False))
        .options(selectinload(ProcurementPayableRequest.procurement_entry))
    )
    return result.scalar_one_or_none()


async def get_active_request_by_entry(db: AsyncSession, entry_id: UUID) -> ProcurementPayableRequest | None:
    result = await db.execute(
        select(ProcurementPayableRequest)
        .where(
            ProcurementPayableRequest.procurement_entry_id == entry_id,
            ProcurementPayableRequest.is_deleted.is_(False),
            ProcurementPayableRequest.payable_entry_id.is_(None),
            ProcurementPayableRequest.approval_status.in_(("pending", "approved")),
        )
        .order_by(ProcurementPayableRequest.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_requests(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    approval_status: str | None = None,
    entry_id: UUID | None = None,
) -> tuple[int, list[ProcurementPayableRequest]]:
    filters = [ProcurementPayableRequest.is_deleted.is_(False)]
    if approval_status:
        filters.append(ProcurementPayableRequest.approval_status == approval_status)
    if entry_id is not None:
        filters.append(ProcurementPayableRequest.procurement_entry_id == entry_id)

    total = int(
        (await db.execute(select(func.count()).select_from(ProcurementPayableRequest).where(*filters))).scalar_one()
    )
    rows = (
        await db.execute(
            select(ProcurementPayableRequest)
            .where(*filters)
            .options(selectinload(ProcurementPayableRequest.procurement_entry))
            .order_by(ProcurementPayableRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return total, list(rows)


async def create_request(db: AsyncSession, data: dict) -> ProcurementPayableRequest:
    obj = ProcurementPayableRequest(**data)
    db.add(obj)
    await db.flush()
    return obj


async def save_request(db: AsyncSession, obj: ProcurementPayableRequest) -> ProcurementPayableRequest:
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


