"""In-process user realtime hub (SSE/WebSocket). No external broker."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from uuid import UUID


class UserRealtimeHub:
    def __init__(self) -> None:
        self._queues: dict[UUID, list[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, user_id: UUID, *, transport: str = "ws") -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._queues[user_id].append(queue)
        try:
            from app.core.enterprise_metrics import enterprise_metrics

            enterprise_metrics.inc_connection(transport, 1)
        except Exception:
            pass
        return queue

    async def unsubscribe(self, user_id: UUID, queue: asyncio.Queue, *, transport: str = "ws") -> None:
        async with self._lock:
            subs = self._queues.get(user_id, [])
            if queue in subs:
                subs.remove(queue)
            if not subs:
                self._queues.pop(user_id, None)
        try:
            from app.core.enterprise_metrics import enterprise_metrics

            enterprise_metrics.inc_connection(transport, -1)
        except Exception:
            pass

    async def publish_user(self, user_id: UUID, envelope: dict) -> None:
        async with self._lock:
            targets = list(self._queues.get(user_id, []))
        for q in targets:
            try:
                q.put_nowait(envelope)
            except asyncio.QueueFull:
                pass

    async def publish_all(self, envelope: dict) -> None:
        async with self._lock:
            all_queues = [q for subs in self._queues.values() for q in subs]
        for q in all_queues:
            try:
                q.put_nowait(envelope)
            except asyncio.QueueFull:
                pass


_hub: UserRealtimeHub | None = None


def get_realtime_hub() -> UserRealtimeHub:
    global _hub
    if _hub is None:
        _hub = UserRealtimeHub()
    return _hub
