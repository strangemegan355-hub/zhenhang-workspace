"""The quote-export handler must actually run, because rounds 141-143 rewrote it untested.

`handle_quote_export_requested` no longer reaches into another domain's internals — it calls
`file.application.store_generated_file` and `quote.application.complete_export_task` — and the event-bus knot was broken
underneath it. Nothing exercised it: `handle_quote_export_requested`, `store_generated_file` and `complete_export_task`
each had **zero** occurrences in any test, so the integration suite passed every one of those rounds without touching
the code they changed.

This arranges a quote with a line, drives the handler the way the worker does, and asserts the effect:

    handler -> the file row is stored (MinIO + database) and the export task is completed

**The commit belongs to the caller.** Both application functions are called with `autocommit=False` on purpose, since
the file row and the task update must become durable together, so the handler leaves the transaction open and the
worker commits it. The test commits for that reason — the kind of detail an untested path hides.

The arrangement writes its own quote, version and item and deletes them again, because the seeded database has one
customer and no quotes at all.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

os.environ.setdefault("SECRET_KEY", "integration-baseline-secret-key-32chars")

import pytest  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.domains.events.event_handlers.quote_export_handlers import (  # noqa: E402
    handle_quote_export_requested,
)
from app.models.customer import Customer  # noqa: E402
from app.models.file_center import FileObject  # noqa: E402
from app.models.machine import Machine  # noqa: E402
from app.models.quote import Quote, QuoteExportTask, QuoteItem, QuoteVersion  # noqa: E402
from sqlalchemy import delete, select  # noqa: E402


@pytest.mark.asyncio
async def test_the_export_handler_stores_a_file_and_completes_the_task():
    async with AsyncSessionLocal() as session:
        customer = (await session.execute(select(Customer).limit(1))).scalar_one_or_none()
        machine = (await session.execute(select(Machine).limit(1))).scalar_one_or_none()
        if customer is None:
            pytest.skip("no customer in this database, so a quote cannot be arranged")

        quote = Quote(
            quote_no=f"TEST-EXPORT-{datetime.now(UTC).strftime('%H%M%S%f')}",
            title="Export flow test",
            customer_id=customer.id,
            machine_id=machine.id if machine else None,
        )
        session.add(quote)
        await session.flush()
        version = QuoteVersion(quote_id=quote.id, version_no=1, changed_at=datetime.now(UTC), is_current=True)
        session.add(version)
        await session.flush()
        session.add(
            QuoteItem(
                quote_version_id=version.id,
                item_code="T-1",
                item_name="Test line",
                unit="台",
                quantity=Decimal("2"),
                unit_price=Decimal("100"),
                line_total=Decimal("200"),
            )
        )
        task = QuoteExportTask(
            quote_id=quote.id,
            format="pdf",
            status="pending",
            requested_at=datetime.now(UTC),
        )
        session.add(task)
        await session.flush()
        quote_id, task_id = str(quote.id), str(task.id)
        await session.commit()

    try:
        # Drive the handler the way the worker does: a payload with the task id, then the caller's commit.
        async with AsyncSessionLocal() as session:
            await handle_quote_export_requested(session, {"task_id": task_id, "format": "pdf", "created_by": None})
            await session.commit()

        async with AsyncSessionLocal() as session:
            reloaded = (
                await session.execute(select(QuoteExportTask).where(QuoteExportTask.id == UUID(task_id)))
            ).scalar_one()
            assert reloaded.status == "completed", f"the handler left the task at {reloaded.status!r}"
            assert reloaded.file_id is not None, "the task is completed but points at no file"

            stored = (
                await session.execute(select(FileObject).where(FileObject.id == reloaded.file_id))
            ).scalar_one_or_none()
            assert stored is not None, "the file row the handler recorded is not readable"
            assert stored.size_bytes and stored.size_bytes > 0, "the stored object is empty"
            assert stored.object_name.startswith(f"exports/quotes/{quote_id}-{task_id}"), stored.object_name
            assert stored.category == "quote_export"
            assert stored.file_ext == "pdf"
    finally:
        # Delete what this test made, in dependency order, so a re-run starts from the same state.
        async with AsyncSessionLocal() as session:
            await session.execute(delete(FileObject).where(FileObject.object_name.like(f"exports/quotes/{quote_id}-%")))
            await session.execute(delete(QuoteExportTask).where(QuoteExportTask.quote_id == UUID(quote_id)))
            await session.execute(
                delete(QuoteItem).where(
                    QuoteItem.quote_version_id.in_(select(QuoteVersion.id).where(QuoteVersion.quote_id == UUID(quote_id)))
                )
            )
            await session.execute(delete(QuoteVersion).where(QuoteVersion.quote_id == UUID(quote_id)))
            await session.execute(delete(Quote).where(Quote.id == UUID(quote_id)))
            await session.commit()
