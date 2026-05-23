from __future__ import annotations

from uuid import UUID

from app.db.session import AsyncSessionLocal
from app.realtime.envelope import build_event_envelope
from app.realtime.hub import get_realtime_hub
from app.realtime.store import persist_event


async def _persist_and_fanout(
    envelope: dict,
    *,
    audience: str = "broadcast",
    audience_user_id: UUID | None = None,
    audience_department_id: UUID | None = None,
    resource_owner_id: UUID | None = None,
    tenant_id: UUID | None = None,
    user_id: UUID | None = None,
    broadcast: bool = False,
) -> dict:
    async with AsyncSessionLocal() as db:
        await persist_event(
            db,
            envelope,
            audience=audience,
            audience_user_id=audience_user_id,
            audience_department_id=audience_department_id,
            resource_owner_id=resource_owner_id,
            tenant_id=tenant_id,
        )
        await db.commit()

    hub = get_realtime_hub()
    if broadcast:
        await hub.publish_all(envelope)
    if user_id is not None:
        await hub.publish_user(user_id, envelope)
    return envelope


async def push_realtime_event(
    *,
    channel: str,
    kind: str,
    payload: dict | None = None,
    user_id: UUID | None = None,
    broadcast: bool = False,
    audience: str | None = None,
    audience_department_id: UUID | None = None,
    resource_owner_id: UUID | None = None,
    tenant_id: UUID | None = None,
) -> dict:
    body = dict(payload or {})
    body.setdefault("kind", kind)
    envelope = build_event_envelope(channel=channel, kind=kind, payload=body)
    resolved_audience = audience or ("user" if user_id and not broadcast else "broadcast")
    return await _persist_and_fanout(
        envelope,
        audience=resolved_audience,
        audience_user_id=user_id if resolved_audience == "user" else None,
        audience_department_id=audience_department_id,
        resource_owner_id=resource_owner_id,
        tenant_id=tenant_id,
        user_id=user_id,
        broadcast=broadcast,
    )


async def push_notification_event(
    *,
    user_id: UUID,
    notification_id: UUID,
    title: str,
    biz_type: str,
    biz_id: UUID | None = None,
) -> dict:
    return await push_realtime_event(
        channel="notification",
        kind="notification.new",
        user_id=user_id,
        audience="user",
        payload={
            "notification_id": str(notification_id),
            "title": title,
            "biz_type": biz_type,
            "biz_id": str(biz_id) if biz_id else None,
            "receiver_id": str(user_id),
        },
    )


async def push_workflow_transition(
    *,
    quote_id: UUID,
    quote_no: str,
    from_state: str,
    to_state: str,
    action_code: str,
    actor_id: UUID | None = None,
    owner_id: UUID | None = None,
    department_id: UUID | None = None,
) -> None:
    body = {
        "quote_id": str(quote_id),
        "quote_no": quote_no,
        "from_state": from_state,
        "to_state": to_state,
        "action_code": action_code,
        "actor_id": str(actor_id) if actor_id else None,
        "owner_id": str(owner_id) if owner_id else None,
    }
    await push_realtime_event(
        channel="workflow",
        kind="workflow.transition",
        payload=body,
        broadcast=True,
        resource_owner_id=owner_id,
        audience_department_id=department_id,
    )
    await push_realtime_event(
        channel="quote",
        kind="quote.state_changed",
        payload=body,
        broadcast=True,
        resource_owner_id=owner_id,
        audience_department_id=department_id,
    )
    await push_realtime_event(
        channel="audit",
        kind="dashboard.refresh",
        payload={"reason": "workflow"},
        broadcast=True,
    )
    await push_realtime_event(
        channel="audit",
        kind="workshop.board_refresh",
        payload={"reason": "workflow", "quote_no": quote_no},
        broadcast=True,
    )


async def push_quote_export_status(
    *,
    user_id: UUID,
    task_id: UUID,
    quote_id: UUID,
    quote_no: str,
    status: str,
    file_id: UUID | None = None,
    owner_id: UUID | None = None,
) -> None:
    body = {
        "task_id": str(task_id),
        "quote_id": str(quote_id),
        "quote_no": quote_no,
        "status": status,
        "file_id": str(file_id) if file_id else None,
        "owner_id": str(owner_id) if owner_id else None,
    }
    await push_realtime_event(
        channel="quote",
        kind="quote.export",
        user_id=user_id,
        audience="user",
        payload=body,
        resource_owner_id=owner_id,
    )
    await push_realtime_event(
        channel="quote",
        kind="quote.export",
        payload=body,
        broadcast=True,
        resource_owner_id=owner_id,
    )
    await push_realtime_event(
        channel="audit",
        kind="dashboard.refresh",
        payload={"reason": "export"},
        broadcast=True,
    )


async def push_quote_updated(
    *,
    quote_id: UUID,
    quote_no: str,
    event: str = "quote.updated",
    owner_id: UUID | None = None,
    department_id: UUID | None = None,
) -> None:
    body = {"quote_id": str(quote_id), "quote_no": quote_no, "owner_id": str(owner_id) if owner_id else None}
    await push_realtime_event(
        channel="quote",
        kind=event,
        payload=body,
        broadcast=True,
        resource_owner_id=owner_id,
        audience_department_id=department_id,
    )
    await push_realtime_event(
        channel="audit",
        kind="dashboard.refresh",
        payload={"reason": event},
        broadcast=True,
    )
    await push_realtime_event(
        channel="audit",
        kind="workshop.board_refresh",
        payload={"reason": event, "quote_no": quote_no},
        broadcast=True,
    )
