from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aftersales_service_request import AfterSalesServiceRequest


async def generate_request_no(db: AsyncSession) -> str:
    prefix = f"AS-{date.today().strftime('%Y%m%d')}-"
    count = int(
        (await db.execute(
            select(func.count()).select_from(AfterSalesServiceRequest).where(
                AfterSalesServiceRequest.request_no.like(f"{prefix}%"),
                AfterSalesServiceRequest.is_deleted.is_(False),
            )
        )).scalar_one()
    )
    return f"{prefix}{count + 1:03d}"


async def get_request(
    db: AsyncSession, request_id: UUID, predicate=None
) -> AfterSalesServiceRequest | None:
    stmt = select(AfterSalesServiceRequest).where(
        AfterSalesServiceRequest.id == request_id,
        AfterSalesServiceRequest.is_deleted.is_(False),
    )
    if predicate is not None:
        stmt = stmt.where(predicate)
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_request(db: AsyncSession, data: dict) -> AfterSalesServiceRequest:
    obj = AfterSalesServiceRequest(**data)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def save_request(db: AsyncSession, obj: AfterSalesServiceRequest) -> AfterSalesServiceRequest:
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_requests(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    customer_id: UUID | None = None,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: UUID | None = None,
    predicate=None,
) -> tuple[int, list[AfterSalesServiceRequest]]:
    filters = [AfterSalesServiceRequest.is_deleted.is_(False)]
    if predicate is not None:
        filters.append(predicate)
    if customer_id is not None:
        filters.append(AfterSalesServiceRequest.customer_id == customer_id)
    if status:
        filters.append(AfterSalesServiceRequest.status == status)
    if priority:
        filters.append(AfterSalesServiceRequest.priority == priority)
    if assigned_to is not None:
        filters.append(AfterSalesServiceRequest.assigned_to == assigned_to)

    total = int(
        (await db.execute(select(func.count()).select_from(AfterSalesServiceRequest).where(*filters))).scalar_one()
    )
    rows = (
        await db.execute(
            select(AfterSalesServiceRequest)
            .where(*filters)
            .order_by(AfterSalesServiceRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return total, list(rows)
