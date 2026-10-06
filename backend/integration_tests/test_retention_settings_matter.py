"""The retention settings must *drive* the cycle, not merely be read by it.

`test_realtime_retention.py` seeds its fixtures *from* `settings.realtime_hot_retention_days`, so it proves the
current value is honoured — but a hardcoded `timedelta(days=7)` would pass it too, because 7 is the default.
What distinguishes "reads the setting" from "uses the default" is running the same data under two values and
getting two different outcomes.

That is what this does, for three settings:

* `realtime_retention_batch_size` bounds one cycle — with it at 1, three stale events yield exactly one archive.
* `realtime_hot_retention_days` decides which events are stale — the *same* three-day-old event is archived at 1
  and left alone at 5.
* `realtime_archive_retention_days` decides which archives are purged — a row archived two days ago survives at 5
  and is purged at 1.

`retention.py` reads the settings inside `hot_cutoff()`/`archive_purge_cutoff()`, at call time rather than at
import, which is what makes this testable at all.
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
        kind="retention-settings",
        envelope={"probe": True},
        audience="broadcast",
        created_at=created_at,
    )


async def _cleanup(marker: str, archive_sequences: list[int]) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(delete(RealtimeEvent).where(RealtimeEvent.channel == marker))
        await db.execute(delete(RealtimeEventArchive).where(RealtimeEventArchive.channel == marker))
        for sequence in archive_sequences:
            await db.execute(delete(RealtimeEventArchive).where(RealtimeEventArchive.sequence == sequence))
        await db.commit()


async def test_the_retention_settings_drive_the_cycle(monkeypatch):
    marker = f"set-{uuid.uuid4().hex[:12]}"
    now = datetime.now(UTC)
    three_days_ago = now - timedelta(days=3)
    archive_sequence = -(uuid.uuid4().int % 1_000_000 + 1)

    # Three stale events and one fresh one, all under this test's marker.
    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                _event(marker, three_days_ago),
                _event(marker, three_days_ago - timedelta(minutes=1)),
                _event(marker, three_days_ago - timedelta(minutes=2)),
                _event(marker, now),
            ]
        )
        db.add(
            RealtimeEventArchive(
                sequence=archive_sequence,
                event_id=uuid.uuid4(),
                channel=marker,
                kind="retention-settings",
                envelope={"probe": True},
                audience="broadcast",
                created_at=three_days_ago,
                archived_at=now - timedelta(days=2),
            )
        )
        await db.commit()

    async def _counts() -> tuple[int, int]:
        async with AsyncSessionLocal() as db:
            hot = len((await db.execute(select(RealtimeEvent).where(RealtimeEvent.channel == marker))).scalars().all())
            archived = len(
                (
                    await db.execute(select(RealtimeEventArchive).where(RealtimeEventArchive.channel == marker))
                ).scalars().all()
            )
            return hot, archived

    try:
        # 1. The batch size bounds one cycle: three stale events, one archived.
        monkeypatch.setattr(settings, "realtime_hot_retention_days", 1)
        monkeypatch.setattr(settings, "realtime_retention_batch_size", 1)
        monkeypatch.setattr(settings, "realtime_archive_retention_days", 30)
        async with AsyncSessionLocal() as db:
            first = await run_retention_cycle(db)
        assert first["archived"] == 1, (
            f"realtime_retention_batch_size=1 must bound one cycle to a single archive, got {first}"
        )
        hot, archived = await _counts()
        assert (hot, archived) == (3, 2), (
            f"after one bounded cycle expected 3 hot and 2 archived (1 seeded), got {hot} hot and {archived}"
        )

        # 2. The same cycle again takes the next one, which shows the limit is per cycle rather than a total.
        async with AsyncSessionLocal() as db:
            second = await run_retention_cycle(db)
        assert second["archived"] == 1, f"the next cycle should take one more, got {second}"

        # 3. The hot window decides which events are stale: the same three-day-old events are left alone at 5.
        monkeypatch.setattr(settings, "realtime_hot_retention_days", 5)
        monkeypatch.setattr(settings, "realtime_retention_batch_size", 100)
        async with AsyncSessionLocal() as db:
            wide = await run_retention_cycle(db)
        assert wide["archived"] == 0, (
            "with realtime_hot_retention_days=5 a three-day-old event is inside the window and must not be "
            f"archived, but {wide} happened"
        )
        hot, archived = await _counts()
        assert (hot, archived) == (2, 3), f"expected 2 hot and 3 archived, got {hot} and {archived}"

        # 4. And at 1 the last stale event goes, so the same data yields opposite outcomes depending on the
        # setting alone. Only one is left: the two bounded cycles above already took the other two.
        monkeypatch.setattr(settings, "realtime_hot_retention_days", 1)
        async with AsyncSessionLocal() as db:
            narrow = await run_retention_cycle(db)
        assert narrow["archived"] == 1, (
            f"with realtime_hot_retention_days=1 the last stale event must be archived, got {narrow}"
        )
        hot, _ = await _counts()
        assert hot == 1, f"only the fresh event should remain hot, got {hot}"

        # 5. The archive window decides purging: the two-day-old archive row survives at 5.
        monkeypatch.setattr(settings, "realtime_archive_retention_days", 5)
        async with AsyncSessionLocal() as db:
            kept = await run_retention_cycle(db)
        assert kept["purged"] == 0, (
            f"with realtime_archive_retention_days=5 a two-day-old archive row must survive, got {kept}"
        )
        _, archived = await _counts()
        assert archived >= 1, "the seeded archive row should still exist"

        # 6. And is purged at 1.
        monkeypatch.setattr(settings, "realtime_archive_retention_days", 1)
        async with AsyncSessionLocal() as db:
            purged = await run_retention_cycle(db)
        assert purged["purged"] >= 1, (
            f"with realtime_archive_retention_days=1 the two-day-old archive row must be purged, got {purged}"
        )
    finally:
        await _cleanup(marker, [archive_sequence])
