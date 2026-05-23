from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_event import DomainEvent


async def create_domain_event(db: AsyncSession, data: dict, *, autocommit: bool = True) -> DomainEvent:
    obj = DomainEvent(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def mark_domain_event_processed(db: AsyncSession, event: DomainEvent, *, autocommit: bool = True) -> None:
    event.status = "processed"
    event.processed_at = datetime.now(UTC)
    await db.flush()
    if autocommit:
        await db.commit()


async def mark_domain_event_failed(
    db: AsyncSession,
    event: DomainEvent,
    error_message: str,
    *,
    autocommit: bool = True,
) -> None:
    event.status = "failed"
    event.retry_count += 1
    event.error_message = error_message
    event.processed_at = datetime.now(UTC)
    await db.flush()
    if autocommit:
        await db.commit()


async def mark_domain_event_dead_letter(db: AsyncSession, event: DomainEvent, *, autocommit: bool = True) -> None:
    event.dead_letter = True
    event.status = "dead_letter"
    event.processed_at = datetime.now(UTC)
    await db.flush()
    if autocommit:
        await db.commit()


async def list_events_for_replay(db: AsyncSession, *, event_type: str | None = None, limit: int = 100) -> list[DomainEvent]:
    stmt = select(DomainEvent).where(
        DomainEvent.is_deleted.is_(False),
        DomainEvent.dead_letter.is_(True),
    )
    if event_type:
        stmt = stmt.where(DomainEvent.event_type == event_type)
    stmt = stmt.order_by(DomainEvent.published_at.asc()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def list_pending_events(db: AsyncSession, *, event_type: str | None = None, limit: int = 100) -> list[DomainEvent]:
    stmt = select(DomainEvent).where(
        DomainEvent.is_deleted.is_(False),
        DomainEvent.status == "pending",
        DomainEvent.dead_letter.is_(False),
    )
    if event_type:
        stmt = stmt.where(DomainEvent.event_type == event_type)
    stmt = stmt.order_by(DomainEvent.published_at.asc()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def get_domain_event(db: AsyncSession, event_id) -> DomainEvent | None:
    stmt = select(DomainEvent).where(DomainEvent.id == event_id, DomainEvent.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def reset_event_for_replay(db: AsyncSession, event: DomainEvent, *, autocommit: bool = True) -> None:
    event.dead_letter = False
    event.status = "pending"
    event.error_message = None
    await db.flush()
    if autocommit:
        await db.commit()
