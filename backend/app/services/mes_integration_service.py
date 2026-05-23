"""MES / OEE integration foundation — ingest and read equipment signals."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.mes import MesEquipmentSignal, MesOeeSnapshot


async def ingest_equipment_signal(
    db: AsyncSession,
    *,
    equipment_code: str,
    signal_key: str,
    signal_value: float,
    unit: str | None = None,
    source: str = "mes",
    tenant_id: UUID | None = None,
    meta: dict | None = None,
) -> MesEquipmentSignal:
    row = MesEquipmentSignal(
        equipment_code=equipment_code,
        signal_key=signal_key,
        signal_value=signal_value,
        unit=unit,
        source=source,
        tenant_id=tenant_id,
        collected_at=datetime.now(UTC),
        meta=meta,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def list_recent_signals(
    db: AsyncSession,
    *,
    equipment_code: str | None = None,
    limit: int = 50,
) -> list[MesEquipmentSignal]:
    stale_before = datetime.now(UTC) - timedelta(seconds=settings.mes_signal_stale_seconds)
    stmt = (
        select(MesEquipmentSignal)
        .where(MesEquipmentSignal.is_deleted.is_(False), MesEquipmentSignal.collected_at >= stale_before)
        .order_by(desc(MesEquipmentSignal.collected_at))
        .limit(limit)
    )
    if equipment_code:
        stmt = stmt.where(MesEquipmentSignal.equipment_code == equipment_code)
    return list((await db.execute(stmt)).scalars().all())


async def record_oee_snapshot(
    db: AsyncSession,
    *,
    line_id: str,
    availability: float,
    performance: float,
    quality: float,
    tenant_id: UUID | None = None,
    source: str = "erp",
) -> MesOeeSnapshot:
    now = datetime.now(UTC)
    oee = round((availability * performance * quality) / 10000, 4)
    row = MesOeeSnapshot(
        line_id=line_id,
        period_start=now - timedelta(hours=1),
        period_end=now,
        availability=availability,
        performance=performance,
        quality=quality,
        oee=oee,
        source=source,
        tenant_id=tenant_id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def latest_oee_by_line(db: AsyncSession) -> dict[str, dict]:
    stmt = select(MesOeeSnapshot).where(MesOeeSnapshot.is_deleted.is_(False)).order_by(desc(MesOeeSnapshot.period_end))
    rows = list((await db.execute(stmt)).scalars().all())
    out: dict[str, dict] = {}
    for r in rows:
        if r.line_id not in out:
            out[r.line_id] = {
                "availability": float(r.availability),
                "performance": float(r.performance),
                "quality": float(r.quality),
                "oee": float(r.oee),
                "source": r.source,
                "period_end": r.period_end.isoformat(),
            }
    return out
