import asyncio
from time import perf_counter
from uuid import UUID

from app.core.enterprise_metrics import enterprise_metrics
from app.db.session import AsyncSessionLocal
from app.domains.events.application.event_bus import event_bus
from app.domains.events.application.register_handlers import register_default_event_handlers
from app.domains.events.repositories.task_queue_repository import (
    mark_task_done,
    mark_task_failed,
    mark_task_running,
    pick_pending_tasks,
)


async def run_event_worker(poll_seconds: float = 1.0) -> None:
    register_default_event_handlers()
    while True:
        async with AsyncSessionLocal() as db:
            tasks = await pick_pending_tasks(db, queue_name="domain_events", limit=20)
            if not tasks:
                await asyncio.sleep(poll_seconds)
                continue
            processed = 0
            failures = 0
            for task in tasks:
                await mark_task_running(db, task, autocommit=False)
                started = perf_counter()
                try:
                    if task.task_type == "domain_event.dispatch" and task.payload:
                        event_id = UUID(str(task.payload["event_id"]))
                        await event_bus.dispatch_by_id(db, event_id=event_id)
                    await mark_task_done(db, task, autocommit=False)
                    processed += 1
                    if task.task_type == "domain_event.dispatch":
                        elapsed = (perf_counter() - started) * 1000
                        if "quote.export" in str(task.payload):
                            enterprise_metrics.record_export(duration_ms=elapsed, failed=False)
                except Exception as exc:
                    await mark_task_failed(db, task, str(exc), autocommit=False)
                    failures += 1
                    enterprise_metrics.record_export(duration_ms=0, failed=True)
            await db.commit()
            enterprise_metrics.record_worker_batch(processed=processed, failures=failures)


def main() -> None:
    asyncio.run(run_event_worker())


if __name__ == "__main__":
    main()
