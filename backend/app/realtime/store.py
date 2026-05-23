from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.realtime_event import RealtimeEvent
from app.realtime.acl import RealtimeACLContext, can_deliver_envelope


async def persist_event(
    db: AsyncSession,
    envelope: dict,
    *,
    audience: str = "broadcast",
    audience_user_id: UUID | None = None,
    audience_department_id: UUID | None = None,
    resource_owner_id: UUID | None = None,
    tenant_id: UUID | None = None,
) -> int:
    payload = envelope.get("payload") or {}
    kind = str(payload.get("kind", "")) if isinstance(payload, dict) else ""
    row = RealtimeEvent(
        event_id=UUID(str(envelope["event_id"])),
        channel=str(envelope.get("channel", "notification")),
        kind=kind,
        envelope=envelope,
        audience=audience,
        audience_user_id=audience_user_id,
        audience_department_id=audience_department_id,
        resource_owner_id=resource_owner_id,
        tenant_id=tenant_id,
    )
    db.add(row)
    await db.flush()
    sequence = int(row.sequence)
    envelope["meta"] = {
        **(envelope.get("meta") or {}),
        "sequence": sequence,
        "cursor": str(sequence),
    }
    return sequence


async def replay_events(
    db: AsyncSession,
    ctx: RealtimeACLContext,
    *,
    after_sequence: int | None = None,
    after_event_id: UUID | None = None,
    channels: list[str] | None = None,
    limit: int = 200,
    tenant_id: UUID | None = None,
) -> list[dict]:
    if after_event_id and after_sequence is None:
        anchor = (
            await db.execute(select(RealtimeEvent.sequence).where(RealtimeEvent.event_id == after_event_id))
        ).scalar_one_or_none()
        if anchor is not None:
            after_sequence = int(anchor)

    replay_since = datetime.now(UTC) - timedelta(days=settings.realtime_replay_retention_days)
    stmt = (
        select(RealtimeEvent)
        .where(RealtimeEvent.created_at >= replay_since)
        .order_by(RealtimeEvent.sequence.asc())
        .limit(min(limit, 500))
    )
    if after_sequence is not None:
        stmt = stmt.where(RealtimeEvent.sequence > after_sequence)
    if channels:
        stmt = stmt.where(RealtimeEvent.channel.in_(channels))
    if tenant_id is not None:
        stmt = stmt.where((RealtimeEvent.tenant_id == tenant_id) | (RealtimeEvent.tenant_id.is_(None)))

    rows = list((await db.execute(stmt)).scalars().all())
    out: list[dict] = []
    for row in rows:
        env = dict(row.envelope)
        env.setdefault("meta", {})
        env["meta"]["sequence"] = int(row.sequence)
        env["meta"]["cursor"] = str(row.sequence)
        if not can_deliver_envelope(
            ctx,
            env,
            audience=row.audience,
            audience_user_id=row.audience_user_id,
            audience_department_id=row.audience_department_id,
            resource_owner_id=row.resource_owner_id,
        ):
            continue
        if channels and env.get("channel") not in channels:
            continue
        out.append(env)
    return out
