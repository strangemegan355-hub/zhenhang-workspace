"""The dispatch test, exercising the worker's path instead of a loop I invented.

`backend/workers/event_worker.py` is the documented mechanism: it picks tasks from the
`domain_events` queue, dispatches each event by id and marks the task done. This reproduces exactly
that (minus the metrics calls) so the test proves the path production actually runs:

    publish -> queued dispatch task -> worker picks it -> handler -> audit row

It still asserts the audit row is absent before the cycle and present after, so the row is provably
written by the dispatch rather than by the publish.
"""

from __future__ import annotations

import os
from uuid import UUID, uuid4

os.environ.setdefault("SECRET_KEY", "integration-baseline-secret-key-32chars")

import pytest  # noqa: E402
from sqlalchemy import delete, func, select, text  # noqa: E402

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.domains.events.application import event_bus, register_default_event_handlers  # noqa: E402
from app.domains.events.repositories.task_queue_repository import (  # noqa: E402
    mark_task_done,
    mark_task_running,
    pick_pending_tasks,
)
from app.models.audit import AuditLog  # noqa: E402

ACTION = "domain_event.quote_created"


@pytest.fixture(autouse=True)
def handlers_registered():
    """`run_event_worker` does this at startup; a test process has to ask for the same thing."""
    register_default_event_handlers()


async def _run_one_worker_cycle() -> int:
    """What `workers/event_worker.py` does for a batch, without the metrics bookkeeping."""
    processed = 0
    async with AsyncSessionLocal() as db:
        tasks = await pick_pending_tasks(db, queue_name="domain_events", limit=20)
        for task in tasks:
            await mark_task_running(db, task, autocommit=False)
            if task.task_type == "domain_event.dispatch" and task.payload:
                event_id = UUID(str(task.payload["event_id"]))
                await event_bus.dispatch_by_id(db, event_id=event_id)
            await mark_task_done(db, task, autocommit=False)
            processed += 1
        await db.commit()
    return processed


async def _count_audit_rows(resource_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == ACTION, AuditLog.resource_id == resource_id)
        )
        return result.scalar() or 0


async def _cleanup(resource_id):
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


async def test_the_worker_dispatches_a_published_event_and_it_writes_its_audit_row():
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

    assert await _count_audit_rows(quote_id) == 0, "the handler must not have run yet"

    try:
        processed = await _run_one_worker_cycle()
        assert processed >= 1, "the publish should have queued a dispatch task"

        found = await _count_audit_rows(quote_id)
        assert found == 1, (
            "the worker's dispatch did not run handle_quote_created, so a published event never "
            "audits — the exact failure the trial guide warns about"
        )
    finally:
        await _cleanup(quote_id)
