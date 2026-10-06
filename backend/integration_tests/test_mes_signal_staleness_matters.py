"""The MES staleness window and the MES switch must change what the board shows.

Round 98's method: the same data under two settings values must produce opposite outcomes, which no hardcoded
value can do. `mes_signal_stale_seconds` (default 120) decides which signals `list_recent_signals` returns, and
the workshop board renders that list only when `mes_enabled` is true.

So one signal collected ninety seconds ago is the whole fixture: at a thirty-second window it must be invisible,
and at a ten-minute window it must appear. A hardcoded 120 would show it in the first case and fail there. Then
the same board call with `mes_enabled` off must render no signals at all, and with it on must render them — the
switch proven the same way, through the code path that actually reads it.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import delete

os.environ["DATABASE_URL"] = os.getenv(
    "INTEGRATION_DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:55432/erp_db"
)
os.environ.setdefault("SECRET_KEY", "integration-secret-key-32-chars-long!")

from app.config.settings import settings  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.mes import MesEquipmentSignal  # noqa: E402
from app.services.mes_integration_service import list_recent_signals  # noqa: E402
from app.services.workshop_board_service import get_workshop_board  # noqa: E402


async def _seed(marker: str, collected_at: datetime) -> None:
    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                MesEquipmentSignal(
                    equipment_code=marker,
                    signal_key=f"probe-{index}",
                    signal_value=float(index),
                    unit="kW",
                    collected_at=collected_at,
                    meta={"probe": True},
                )
                for index in (1, 2)
            ]
        )
        await db.commit()


async def _cleanup(marker: str) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(delete(MesEquipmentSignal).where(MesEquipmentSignal.equipment_code == marker))
        await db.commit()


async def test_the_mes_staleness_window_and_switch_drive_the_board(monkeypatch):
    marker = f"mes-{uuid.uuid4().hex[:12]}"
    ninety_seconds_ago = datetime.now(UTC) - timedelta(seconds=90)
    await _seed(marker, ninety_seconds_ago)

    try:
        # 0. The control that makes the next step mean something: under the real default (120) the same call
        # sees both rows, so the empty result below is the setting's doing and not a missing fixture.
        assert settings.mes_signal_stale_seconds == 120, (
            f"this control assumes the shipped default of 120, found {settings.mes_signal_stale_seconds}"
        )
        async with AsyncSessionLocal() as db:
            default_window = await list_recent_signals(db, equipment_code=marker)
        assert len(default_window) == 2, (
            f"the ninety-second-old signals must be visible under the default 120-second window, got "
            f"{len(default_window)} — without this the next assertion would pass on empty data"
        )

        # 1. A thirty-second window must hide a ninety-second-old signal.
        monkeypatch.setattr(settings, "mes_signal_stale_seconds", 30)
        async with AsyncSessionLocal() as db:
            narrow = await list_recent_signals(db, equipment_code=marker)
        assert narrow == [], (
            "with mes_signal_stale_seconds=30 a ninety-second-old signal must not be listed; a hardcoded 120 "
            f"would list it, so finding {len(narrow)} row(s) means the setting is ignored"
        )

        # 2. The same signal under a ten-minute window must appear.
        monkeypatch.setattr(settings, "mes_signal_stale_seconds", 600)
        async with AsyncSessionLocal() as db:
            wide = await list_recent_signals(db, equipment_code=marker)
        assert len(wide) == 2, (
            f"with mes_signal_stale_seconds=600 both seeded signals must be listed, got {len(wide)}"
        )

        # 3. The board path honours the switch: the caller is only there for the work-order summary's scope.
        caller = SimpleNamespace(id=uuid.uuid4(), roles=[], is_superuser=False)
        monkeypatch.setattr(settings, "mes_enabled", True)
        async with AsyncSessionLocal() as db:
            board_on = await get_workshop_board(db, caller)
        codes_on = {row["equipment_code"] for row in board_on.get("mes_signals", [])}
        assert marker in codes_on, (
            "with mes_enabled=True the board must render the fresh signal; "
            f"equipment codes seen: {sorted(codes_on)[:5]}"
        )

        monkeypatch.setattr(settings, "mes_enabled", False)
        async with AsyncSessionLocal() as db:
            board_off = await get_workshop_board(db, caller)
        assert board_off.get("mes_signals") == [], (
            f"with mes_enabled=False the board must render no signals, got {len(board_off.get('mes_signals') or [])}"
        )
    finally:
        await _cleanup(marker)
