"""
Realtime event lifecycle: hot TTL → archive → purge.

Partition strategy (operations):
  - Phase 1 (current): time-indexed hot table + archive table + batch move/delete.
  - Phase 2 (scale): PostgreSQL RANGE partition on realtime_events(created_at) by month;
    detach old partitions into archive tablespace. See docs/ENTERPRISE_DEPLOYMENT.md.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.realtime_event import RealtimeEvent
from app.models.realtime_event_archive import RealtimeEventArchive


def hot_cutoff() -> datetime:
    return datetime.now(UTC) - timedelta(days=settings.realtime_hot_retention_days)


def archive_purge_cutoff() -> datetime:
    return datetime.now(UTC) - timedelta(days=settings.realtime_archive_retention_days)


async def archive_stale_events(db: AsyncSession) -> int:
    """Move events older than hot retention from hot table to archive."""
    cutoff = hot_cutoff()
    batch = settings.realtime_retention_batch_size
    rows = list(
        (
            await db.execute(
                select(RealtimeEvent)
                .where(RealtimeEvent.created_at < cutoff)
                .order_by(RealtimeEvent.sequence.asc())
                .limit(batch)
            )
        ).scalars().all()
    )
    if not rows:
        return 0

    now = datetime.now(UTC)
    archive_rows = [
        {
            "sequence": r.sequence,
            "event_id": r.event_id,
            "channel": r.channel,
            "kind": r.kind,
            "envelope": r.envelope,
            "audience": r.audience,
            "audience_user_id": r.audience_user_id,
            "audience_department_id": r.audience_department_id,
            "resource_owner_id": r.resource_owner_id,
            "tenant_id": getattr(r, "tenant_id", None),
            "created_at": r.created_at,
            "archived_at": now,
        }
        for r in rows
    ]
    db.add_all([RealtimeEventArchive(**row) for row in archive_rows])
    seqs = [r.sequence for r in rows]
    await db.execute(delete(RealtimeEvent).where(RealtimeEvent.sequence.in_(seqs)))
    await db.flush()
    return len(rows)


async def purge_old_archives(db: AsyncSession) -> int:
    cutoff = archive_purge_cutoff()
    result = await db.execute(delete(RealtimeEventArchive).where(RealtimeEventArchive.archived_at < cutoff))
    return int(result.rowcount or 0)


async def count_hot_and_archive(db: AsyncSession) -> tuple[int, int]:
    hot = int((await db.execute(select(func.count()).select_from(RealtimeEvent))).scalar_one())
    try:
        archive = int((await db.execute(select(func.count()).select_from(RealtimeEventArchive))).scalar_one())
    except Exception:
        archive = 0
    return hot, archive


async def run_retention_cycle(db: AsyncSession) -> dict:
    archived = await archive_stale_events(db)
    purged = await purge_old_archives(db)
    await db.commit()
    return {"archived": archived, "purged": purged}


async def max_hot_sequence(db: AsyncSession) -> int | None:
    val = (await db.execute(select(func.max(RealtimeEvent.sequence)))).scalar_one_or_none()
    return int(val) if val is not None else None
