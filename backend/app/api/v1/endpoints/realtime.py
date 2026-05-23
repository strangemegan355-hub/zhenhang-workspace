import asyncio
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.realtime.acl import RealtimeACLContext, build_acl_context, can_deliver_envelope, filter_subscribed_channels
from app.realtime.envelope import build_heartbeat_envelope, build_subscribe_ack
from app.realtime.hub import get_realtime_hub
from app.core.enterprise_metrics import enterprise_metrics
from app.realtime.retention import max_hot_sequence
from app.realtime.store import replay_events
from app.repositories.user_repository import get_user_by_id

router = APIRouter()

DEFAULT_CHANNELS = ["notification", "workflow", "quote", "audit"]


async def _load_acl_context(db: AsyncSession, user_id: UUID) -> RealtimeACLContext | None:
    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        return None
    return build_acl_context(user)


def _user_id_from_token(token: str) -> UUID:
    payload = decode_access_token(token)
    if payload is None or payload.get("sub") is None:
        raise ValueError("invalid token")
    return UUID(str(payload["sub"]))


def _parse_channels(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_CHANNELS)
    return [c.strip() for c in raw.split(",") if c.strip()]


def _cursor_from_request(
    request: Request,
    *,
    last_event_id: str | None,
    after_sequence: int | None,
) -> tuple[int | None, UUID | None]:
    header_id = request.headers.get("last-event-id") or request.headers.get("Last-Event-ID")
    event_id_raw = last_event_id or header_id
    event_uuid: UUID | None = None
    if event_id_raw:
        try:
            event_uuid = UUID(str(event_id_raw))
        except (ValueError, TypeError):
            try:
                after_sequence = int(event_id_raw)
            except (ValueError, TypeError):
                pass
    return after_sequence, event_uuid


def _format_sse(envelope: dict, channel: str) -> str:
    seq = (envelope.get("meta") or {}).get("sequence")
    id_line = f"id: {seq}\n" if seq is not None else f"id: {envelope.get('event_id')}\n"
    return f"{id_line}event: {channel}\ndata: {json.dumps(envelope, ensure_ascii=False)}\n\n"


@router.get("/replay")
async def realtime_replay(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_active_user)],
    after_sequence: int | None = Query(default=None, ge=0),
    last_event_id: str | None = Query(default=None),
    channels: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
) -> dict:
    ctx = build_acl_context(current)
    event_uuid: UUID | None = None
    if last_event_id:
        try:
            event_uuid = UUID(last_event_id)
        except ValueError:
            try:
                after_sequence = int(last_event_id)
            except ValueError:
                pass
    requested = filter_subscribed_channels(_parse_channels(channels), ctx)
    from time import perf_counter

    started = perf_counter()
    events = await replay_events(
        db,
        ctx,
        after_sequence=after_sequence,
        after_event_id=event_uuid,
        channels=requested,
        limit=limit,
        tenant_id=ctx.tenant_id,
    )
    max_seq = await max_hot_sequence(db)
    lag_ms = 0.0
    if max_seq and after_sequence is not None:
        lag_ms = float(max(0, max_seq - after_sequence)) * 10.0
    enterprise_metrics.record_replay(events_count=len(events), lag_ms=lag_ms)
    last_seq = None
    if events:
        last_seq = (events[-1].get("meta") or {}).get("sequence")
    return {
        "events": events,
        "count": len(events),
        "last_sequence": last_seq,
        "allowed_channels": list(ctx.allowed_channels),
        "replay_duration_ms": round((perf_counter() - started) * 1000, 2),
        "replay_lag_ms": lag_ms,
    }


@router.get("/stream")
async def realtime_sse(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    token: str = Query(..., min_length=10),
    channels: str | None = Query(default=None),
    last_event_id: str | None = Query(default=None),
    after_sequence: int | None = Query(default=None, ge=0),
) -> StreamingResponse:
    try:
        user_id = _user_id_from_token(token)
    except (ValueError, TypeError):
        return StreamingResponse(
            iter([f"event: error\ndata: {json.dumps({'message': 'Unauthorized'})}\n\n"]),
            media_type="text/event-stream",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    ctx = await _load_acl_context(db, user_id)
    if ctx is None:
        return StreamingResponse(
            iter([f"event: error\ndata: {json.dumps({'message': 'Forbidden'})}\n\n"]),
            media_type="text/event-stream",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    allowed = set(filter_subscribed_channels(_parse_channels(channels), ctx))
    after_sequence, event_uuid = _cursor_from_request(request, last_event_id=last_event_id, after_sequence=after_sequence)
    hub = get_realtime_hub()
    queue = await hub.subscribe(user_id, transport="sse")
    enterprise_metrics.inc_reconnect()

    async def generator():
        try:
            yield ": connected\n\n"
            missed = await replay_events(
                db,
                ctx,
                after_sequence=after_sequence,
                after_event_id=event_uuid,
                channels=list(allowed),
                limit=200,
                tenant_id=ctx.tenant_id,
            )
            enterprise_metrics.record_replay(events_count=len(missed), lag_ms=0)
            for envelope in missed:
                ch = envelope.get("channel", "notification")
                if ch in allowed:
                    yield _format_sse(envelope, str(ch))

            while True:
                try:
                    envelope = await asyncio.wait_for(queue.get(), timeout=25.0)
                except asyncio.TimeoutError:
                    hb = build_heartbeat_envelope()
                    if "notification" in allowed:
                        yield _format_sse(hb, "notification")
                    continue
                if not can_deliver_envelope(ctx, envelope):
                    continue
                ch = envelope.get("channel", "notification")
                if ch in allowed:
                    yield _format_sse(envelope, str(ch))
        finally:
            await hub.unsubscribe(user_id, queue, transport="sse")

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.websocket("/ws")
async def realtime_ws(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    from app.db.session import AsyncSessionLocal

    await websocket.accept()
    user_id: UUID | None = None
    queue: asyncio.Queue | None = None
    ctx: RealtimeACLContext | None = None
    subscribed: list[str] = list(DEFAULT_CHANNELS)

    try:
        if not token:
            first = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            try:
                msg = json.loads(first)
                token = msg.get("token") or (msg.get("payload") or {}).get("token")
            except json.JSONDecodeError:
                token = first
        if not token:
            await websocket.close(code=4401)
            return
        user_id = _user_id_from_token(token)
        async with AsyncSessionLocal() as db:
            ctx = await _load_acl_context(db, user_id)
        if ctx is None:
            await websocket.close(code=4403)
            return

        subscribed = filter_subscribed_channels(subscribed, ctx)
        hub = get_realtime_hub()
        queue = await hub.subscribe(user_id, transport="ws")
        await websocket.send_json(build_subscribe_ack(subscribed))

        async def reader() -> None:
            nonlocal subscribed
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if msg.get("message_type") == "subscribe":
                    chs = (msg.get("payload") or {}).get("channels")
                    if isinstance(chs, list):
                        subscribed = filter_subscribed_channels([str(c) for c in chs], ctx)
                    await websocket.send_json(build_subscribe_ack(subscribed))
                elif msg.get("message_type") == "heartbeat":
                    await websocket.send_json(build_heartbeat_envelope())
                elif msg.get("message_type") == "reconnect":
                    enterprise_metrics.inc_reconnect()
                    payload = msg.get("payload") or {}
                    last_id = payload.get("last_event_id") or msg.get("event_id")
                    after_seq = payload.get("after_sequence")
                    event_uuid: UUID | None = None
                    if last_id:
                        try:
                            event_uuid = UUID(str(last_id))
                        except ValueError:
                            try:
                                after_seq = int(last_id)
                            except ValueError:
                                pass
                    async with AsyncSessionLocal() as db:
                        missed = await replay_events(
                            db,
                            ctx,
                            after_sequence=after_seq,
                            after_event_id=event_uuid,
                            channels=subscribed,
                            limit=200,
                            tenant_id=ctx.tenant_id,
                        )
                        enterprise_metrics.record_replay(events_count=len(missed), lag_ms=0)
                    for envelope in missed:
                        if can_deliver_envelope(ctx, envelope):
                            await websocket.send_json(envelope)
                    await websocket.send_json(
                        {
                            **build_subscribe_ack(subscribed),
                            "payload": {
                                "replayed": len(missed),
                                "last_event_id": last_id,
                            },
                        }
                    )

        reader_task = asyncio.create_task(reader())
        try:
            while True:
                try:
                    envelope = await asyncio.wait_for(queue.get(), timeout=25.0)
                except asyncio.TimeoutError:
                    await websocket.send_json(build_heartbeat_envelope())
                    continue
                if ctx and not can_deliver_envelope(ctx, envelope):
                    continue
                ch = envelope.get("channel", "notification")
                if ch in subscribed:
                    await websocket.send_json(envelope)
        finally:
            reader_task.cancel()
    except (WebSocketDisconnect, asyncio.TimeoutError, ValueError):
        pass
    finally:
        if user_id and queue:
            await get_realtime_hub().unsubscribe(user_id, queue, transport="ws")
        try:
            await websocket.close()
        except Exception:
            pass
