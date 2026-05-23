"""Periodic maintenance: realtime retention, metrics refresh."""

import asyncio

from app.config.settings import settings
from app.core.enterprise_metrics import enterprise_metrics
from app.db.session import AsyncSessionLocal
from app.realtime.retention import count_hot_and_archive, run_retention_cycle
from sqlalchemy import func, select

from app.models.tasking import TaskQueue


async def run_maintenance_once() -> dict:
    async with AsyncSessionLocal() as db:
        result = await run_retention_cycle(db)
        hot, archive = await count_hot_and_archive(db)
        enterprise_metrics.set_realtime_counts(hot=hot, archive=archive)
        pending = int(
            (
                await db.execute(
                    select(func.count()).select_from(TaskQueue).where(
                        TaskQueue.is_deleted.is_(False),
                        TaskQueue.status == "pending",
                        TaskQueue.dead_letter.is_(False),
                    )
                )
            ).scalar_one()
        )
        dead = int(
            (
                await db.execute(
                    select(func.count()).select_from(TaskQueue).where(
                        TaskQueue.is_deleted.is_(False),
                        TaskQueue.dead_letter.is_(True),
                    )
                )
            ).scalar_one()
        )
        enterprise_metrics.set_queue_backlog(pending=pending, dead_letter=dead)
        enterprise_metrics.record_retention(archived=result["archived"], purged=result["purged"])
        return {**result, "hot_count": hot, "archive_count": archive, "queue_pending": pending}


async def run_maintenance_loop() -> None:
    interval = settings.maintenance_interval_seconds
    while True:
        try:
            await run_maintenance_once()
        except Exception as exc:
            enterprise_metrics.record_worker_batch(processed=0, failures=1)
            print(f"[maintenance] error: {exc}")
        await asyncio.sleep(interval)


def main() -> None:
    asyncio.run(run_maintenance_loop())


if __name__ == "__main__":
    main()
