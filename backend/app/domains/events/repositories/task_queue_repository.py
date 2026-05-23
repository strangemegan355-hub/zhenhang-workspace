from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tasking import TaskQueue


async def enqueue_task(
    db: AsyncSession,
    *,
    queue_name: str,
    task_type: str,
    payload: dict | None,
    created_by: UUID | None,
    delay_seconds: int = 0,
    autocommit: bool = True,
) -> TaskQueue:
    obj = TaskQueue(
        queue_name=queue_name,
        task_type=task_type,
        payload=payload,
        status="pending",
        retry_count=0,
        max_retry=5,
        dead_letter=False,
        available_at=datetime.now(UTC) + timedelta(seconds=delay_seconds),
        created_by=created_by,
    )
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def pick_pending_tasks(db: AsyncSession, *, queue_name: str, limit: int = 50) -> list[TaskQueue]:
    now = datetime.now(UTC)
    stmt = (
        select(TaskQueue)
        .where(
            TaskQueue.is_deleted.is_(False),
            TaskQueue.queue_name == queue_name,
            TaskQueue.status == "pending",
            TaskQueue.dead_letter.is_(False),
            TaskQueue.available_at <= now,
        )
        .order_by(TaskQueue.available_at.asc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def mark_task_running(db: AsyncSession, task: TaskQueue, *, autocommit: bool = True) -> None:
    task.status = "running"
    task.started_at = datetime.now(UTC)
    await db.flush()
    if autocommit:
        await db.commit()


async def mark_task_done(db: AsyncSession, task: TaskQueue, *, autocommit: bool = True) -> None:
    task.status = "completed"
    task.finished_at = datetime.now(UTC)
    await db.flush()
    if autocommit:
        await db.commit()


async def mark_task_failed(db: AsyncSession, task: TaskQueue, error: str, *, autocommit: bool = True) -> None:
    task.retry_count += 1
    task.last_error = error
    if task.retry_count >= task.max_retry:
        task.dead_letter = True
        task.status = "dead_letter"
    else:
        task.status = "pending"
        task.available_at = datetime.now(UTC) + timedelta(seconds=min(2**task.retry_count, 300))
    await db.flush()
    if autocommit:
        await db.commit()
