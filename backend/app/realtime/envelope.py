from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

PROTOCOL_VERSION = "1.0.0"
EVENT_VERSION = "1"

CHANNELS = frozenset({"notification", "workflow", "quote", "audit"})


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def build_event_envelope(*, channel: str, kind: str, payload: dict) -> dict:
    if channel not in CHANNELS:
        channel = "notification"
    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_type": "event",
        "event_version": EVENT_VERSION,
        "channel": channel,
        "event_id": str(uuid4()),
        "timestamp": _now_iso(),
        "payload": {"kind": kind, **payload},
    }


def build_heartbeat_envelope() -> dict:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_type": "heartbeat",
        "event_version": EVENT_VERSION,
        "channel": "notification",
        "event_id": str(uuid4()),
        "timestamp": _now_iso(),
        "payload": {"interval_ms": 15000},
    }


def build_subscribe_ack(channels: list[str]) -> dict:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_type": "subscribe_ack",
        "event_version": EVENT_VERSION,
        "channel": channels[0] if channels else "notification",
        "event_id": str(uuid4()),
        "timestamp": _now_iso(),
        "payload": {"channels": channels, "ok": True},
    }
