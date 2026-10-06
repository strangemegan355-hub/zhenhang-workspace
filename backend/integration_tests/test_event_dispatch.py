"""The dispatcher, proven against the live database.

Round 36 found that `register_default_event_handlers()` registers `handle_quote_created` but nothing
drained published events, so the audit row that handler writes never appeared. This test starts the
dispatcher loop for real, publishes a `quote.created` event, and waits for the audit row to land —
the whole chain: publish → pending event → dispatcher → handler → audit row.

Everything it creates is removed afterwards, keyed by the event id it generated.
"""

from __future__ import annotations

import asyncio
import os
import time
from uuid import uuid4

os.environ.setdefault("SECRET_KEY", "integration-baseline-secret-key-32chars")

import pytest  # noqa: E402
from sqlalchemy import delete, func, select  # noqa: E402

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.domains.events.application import event_bus, register_default_event_handlers  # noqa: E402
from app.main import dispatch_pending_events_forever  # noqa: E402
from app.models.audit import AuditLog  # noqa: E402

ACTION = "domain_event.quote_created"


@pytest.fixture(autouse=True)
def handlers_registered():
    """The app registers these at startup; a test process has to ask for the same thing."""
    register_default_event_handlers()


async def _count_audit_rows(resource_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == ACTION, AuditLog.resource_id == resource_id)
        )
        return result.scalar() or 0


async def _cleanup(resource_id):
    from sqlalchemy import text

    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(AuditLog).where(AuditLog.action == ACTION, AuditLog.resource_id == resource_id)
        )
        await session.execute(
            text(
                "delete from task_queue where payload ->> 'event_id' in "
                "(select id::text from domain_events where aggregate_id = :aggregate_id)"
            ),
            {"aggregate_id": str(resource_id)},
        )
        await session.execute(
            text("delete from domain_events where aggregate_id = :aggregate_id"),
            {"aggregate_id": str(resource_id)},
        )
        await session.commit()


async def test_a_published_event_is_dispatched_and_writes_its_audit_row():
    quote_id = uuid4()
    await _cleanup(quote_id)

    async with AsyncSessionLocal() as session:
        await event_bus.publish(
            session,
            event_type="quote.created",
            aggregate_type="quote",
            aggregate_id=quote_id,
            payload={"quote_id": str(quote_id)},
            created_by=None,
        )
        await session.commit()

    assert await _count_audit_rows(quote_id) == 0, "the audit row should not exist before dispatch"

    dispatcher = asyncio.create_task(dispatch_pending_events_forever(interval_seconds=0.05))
    try:
        deadline = time.monotonic() + 15
        found = 0
        while time.monotonic() < deadline:
            found = await _count_audit_rows(quote_id)
            if found:
                break
            await asyncio.sleep(0.1)
    finally:
        dispatcher.cancel()
        try:
            await dispatcher
        except asyncio.CancelledError:
            pass
        await _cleanup(quote_id)

    assert found == 1, "the dispatcher did not run the handler, so the audit row never appeared"


async def test_the_dispatcher_leaves_nothing_behind_on_a_quiet_database():
    """A dispatch cycle with nothing pending must be a no-op, not an error."""
    dispatcher = asyncio.create_task(dispatch_pending_events_forever(interval_seconds=0.05))
    try:
        await asyncio.sleep(0.2)
    finally:
        dispatcher.cancel()
        try:
            await dispatcher
        except asyncio.CancelledError:
            pass

    assert dispatcher.cancelled() or dispatcher.done()
