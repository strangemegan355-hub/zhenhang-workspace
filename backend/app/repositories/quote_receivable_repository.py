from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quote_receivable_request import QuoteReceivableRequest


async def get_request(db: AsyncSession, request_id: UUID) -> QuoteReceivableRequest | None:
    result = await db.execute(
        select(QuoteReceivableRequest)
        .where(QuoteReceivableRequest.id == request_id, QuoteReceivableRequest.is_deleted.is_(False))
        .options(selectinload(QuoteReceivableRequest.quote))
    )
    return result.scalar_one_or_none()


async def get_active_request_by_quote(db: AsyncSession, quote_id: UUID) -> QuoteReceivableRequest | None:
    result = await db.execute(
        select(QuoteReceivableRequest)
        .where(
            QuoteReceivableRequest.quote_id == quote_id,
            QuoteReceivableRequest.is_deleted.is_(False),
            QuoteReceivableRequest.receivable_entry_id.is_(None),
            QuoteReceivableRequest.approval_status.in_(("pending", "approved", "none")),
        )
        .order_by(QuoteReceivableRequest.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_requests(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    approval_status: str | None = None,
    quote_id: UUID | None = None,
) -> tuple[int, list[QuoteReceivableRequest]]:
    filters = [QuoteReceivableRequest.is_deleted.is_(False)]
    if approval_status:
        filters.append(QuoteReceivableRequest.approval_status == approval_status)
    if quote_id is not None:
        filters.append(QuoteReceivableRequest.quote_id == quote_id)

    from sqlalchemy import func

    total = int((await db.execute(select(func.count()).select_from(QuoteReceivableRequest).where(*filters))).scalar_one())
    rows = (
        await db.execute(
            select(QuoteReceivableRequest)
            .where(*filters)
            .options(selectinload(QuoteReceivableRequest.quote))
            .order_by(QuoteReceivableRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return total, list(rows)


async def create_request(db: AsyncSession, data: dict) -> QuoteReceivableRequest:
    obj = QuoteReceivableRequest(**data)
    db.add(obj)
    await db.flush()
    return obj


async def save_request(db: AsyncSession, obj: QuoteReceivableRequest) -> QuoteReceivableRequest:
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def commit_session(db: AsyncSession) -> None:
    await db.commit()
