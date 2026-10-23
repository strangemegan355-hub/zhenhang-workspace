from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.events.repositories.domain_event_repository import (
    create_domain_event,
    get_domain_event,
    list_events_for_replay,
    list_pending_events,
    mark_domain_event_dead_letter,
    mark_domain_event_failed,
    mark_domain_event_processed,
    reset_event_for_replay,
)
from app.domains.events.repositories.task_queue_repository import enqueue_task

EventHandler = Callable[[AsyncSession, dict], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self.max_retry = 3

    def register(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(
        self,
        db: AsyncSession,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: UUID | None,
        payload: dict | None,
        created_by: UUID | None,
        dispatch_immediately: bool = False,
    ) -> None:
        event = await create_domain_event(
            db,
            {
                "event_type": event_type,
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "payload": _jsonable(payload),
                "status": "pending",
                "published_at": datetime.now(UTC),
                "created_by": created_by,
            },
            autocommit=False,
        )
        await enqueue_task(
            db,
            queue_name="domain_events",
            task_type="domain_event.dispatch",
            payload={"event_id": str(event.id)},
            created_by=created_by,
            autocommit=False,
        )
        if not dispatch_immediately:
            return
        try:
            await self.dispatch_existing_event(db, event=event)
        except Exception:
            # Keep business transaction independent from async event handling failures.
            return

    async def dispatch_existing_event(self, db: AsyncSession, *, event) -> None:
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            await mark_domain_event_processed(db, event, autocommit=False)
            return
        for _ in range(self.max_retry + 1):
            try:
                for handler in handlers:
                    await handler(db, event.payload or {})
                await mark_domain_event_processed(db, event, autocommit=False)
                return
            except Exception as exc:
                await mark_domain_event_failed(db, event, str(exc), autocommit=False)
                if event.retry_count >= self.max_retry:
                    await mark_domain_event_dead_letter(db, event, autocommit=False)
                    raise

    async def replay_dead_letters(self, db: AsyncSession, *, event_type: str | None = None, limit: int = 100) -> dict:
        events = await list_events_for_replay(db, event_type=event_type, limit=limit)
        processed = 0
        failed = 0
        for event in events:
            await reset_event_for_replay(db, event, autocommit=False)
            try:
                await self.dispatch_existing_event(db, event=event)
                processed += 1
            except Exception:
                failed += 1
        return {"requested": len(events), "processed": processed, "failed": failed}

    async def dispatch_by_id(self, db: AsyncSession, *, event_id: UUID) -> None:
        target = await get_domain_event(db, event_id)
        if target is None:
            return
        if target.dead_letter:
            await reset_event_for_replay(db, target, autocommit=False)
        if target.status == "processed":
            return
        if target.status not in {"pending", "failed", "dead_letter"}:
            return
        await self.dispatch_existing_event(db, event=target)

    async def process_pending(self, db: AsyncSession, *, event_type: str | None = None, limit: int = 100) -> dict:
        events = await list_pending_events(db, event_type=event_type, limit=limit)
        processed = 0
        failed = 0
        for event in events:
            try:
                await self.dispatch_existing_event(db, event=event)
                processed += 1
            except Exception:
                failed += 1
        return {"requested": len(events), "processed": processed, "failed": failed}


event_bus = EventBus()


def _jsonable(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value
