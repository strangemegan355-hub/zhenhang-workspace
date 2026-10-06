"""The maintenance worker's retention cycle, with data in it.

The `maintenance` container runs `run_retention_cycle` against the real database on a timer, and until now
no test had ever given it a hot event to archive or an old archive row to purge — running the cycle here
returned `{'archived': 0, 'purged': 0, ...}`, which proves it does not crash and nothing more.

This seeds one fresh event, one event older than the hot retention window, and one archive row older than
the purge window, then asserts what the cycle did: the stale event left the hot table and arrived in the
archive with its payload, the fresh one stayed hot, and the old archive row is gone.

`sequence` is the archive's primary key and is not autoincrementing (it is copied from the hot row for
traceability), so the hand-made old row uses a negative sequence that no autoincrement can reach.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

os.environ["DATABASE_URL"] = os.getenv(
    "INTEGRATION_DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:55432/erp_db"
)
os.environ.setdefault("SECRET_KEY", "integration-secret-key-32-chars-long!")

from app.config.settings import settings  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.realtime_event import RealtimeEvent  # noqa: E402
from app.models.realtime_event_archive import RealtimeEventArchive  # noqa: E402
from app.realtime.retention import run_retention_cycle  # noqa: E402


def _event(channel: str, created_at: datetime) -> RealtimeEvent:
    return RealtimeEvent(
        event_id=uuid.uuid4(),
        channel=channel,
        kind="retention-test",
        envelope={"probe": True},
        audience="broadcast",
        created_at=created_at,
    )


async def _cleanup(marker: str, archive_sequence: int) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(delete(RealtimeEvent).where(RealtimeEvent.channel == marker))
        await db.execute(delete(RealtimeEventArchive).where(RealtimeEventArchive.channel == marker))
        await db.execute(delete(RealtimeEventArchive).where(RealtimeEventArchive.sequence == archive_sequence))
        await db.commit()


async def test_retention_archives_stale_events_and_purges_old_archives():
    # The column is String(32), so the marker has to fit in it.
    marker = f"ret-{uuid.uuid4().hex[:12]}"
    now = datetime.now(UTC)
    stale_at = now - timedelta(days=settings.realtime_hot_retention_days + 1)
    old_archived_at = now - timedelta(days=settings.realtime_archive_retention_days + 1)
    old_archive_sequence = -(uuid.uuid4().int % 1_000_000 + 1)

    fresh = _event(marker, now)
    stale = _event(marker, stale_at)

    try:
        async with AsyncSessionLocal() as db:
            db.add_all([fresh, stale])
            db.add(
                RealtimeEventArchive(
                    sequence=old_archive_sequence,
                    event_id=uuid.uuid4(),
                    channel=marker,
                    kind="retention-test",
                    envelope={"probe": True},
                    audience="broadcast",
                    created_at=stale_at,
                    archived_at=old_archived_at,
                )
            )
            await db.commit()

            result = await run_retention_cycle(db)

        assert result["archived"] >= 1, f"nothing was archived: {result}"
        assert result["purged"] >= 1, f"nothing was purged: {result}"

        async with AsyncSessionLocal() as db:
            hot_ids = set(
                (await db.execute(select(RealtimeEvent.event_id).where(RealtimeEvent.channel == marker)))
                .scalars()
                .all()
            )
            archived = (
                await db.execute(
                    select(RealtimeEventArchive).where(RealtimeEventArchive.event_id == stale.event_id)
                )
            ).scalar_one_or_none()
            old_row = (
                await db.execute(
                    select(RealtimeEventArchive).where(RealtimeEventArchive.sequence == old_archive_sequence)
                )
            ).scalar_one_or_none()

        assert fresh.event_id in hot_ids, "the fresh event must stay in the hot table"
        assert stale.event_id not in hot_ids, "the stale event must leave the hot table"
        assert archived is not None, "the stale event must arrive in the archive"
        assert archived.envelope == {"probe": True}, "the archive must carry the event payload"
        assert archived.channel == marker
        assert old_row is None, "an archive row past the purge window must be deleted"
    finally:
        await _cleanup(marker, old_archive_sequence)


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
