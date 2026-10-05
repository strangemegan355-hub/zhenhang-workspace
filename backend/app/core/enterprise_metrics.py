"""In-process enterprise metrics (no external APM package). Scraped via /health/metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock


@dataclass
class EnterpriseMetrics:
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    _lock: Lock = field(default_factory=Lock, repr=False)

    request_total: int = 0
    error_total: int = 0
    last_request_ms: float = 0.0
    request_latency_sum_ms: float = 0.0

    ws_connections_active: int = 0
    sse_connections_active: int = 0
    reconnect_total: int = 0

    replay_requests_total: int = 0
    replay_events_returned_total: int = 0
    replay_lag_ms_last: float = 0.0

    export_total: int = 0
    export_duration_ms_last: float = 0.0
    export_failures_total: int = 0

    worker_tasks_processed: int = 0
    worker_failures_total: int = 0
    retention_archived_last_run: int = 0
    retention_purged_last_run: int = 0

    queue_backlog_pending: int = 0
    queue_backlog_dead_letter: int = 0

    realtime_events_hot_count: int = 0
    realtime_events_archive_count: int = 0

    def mark_request(self, elapsed_ms: float, is_error: bool) -> None:
        with self._lock:
            self.request_total += 1
            self.last_request_ms = elapsed_ms
            self.request_latency_sum_ms += elapsed_ms
            if is_error:
                self.error_total += 1

    def inc_connection(self, transport: str, delta: int = 1) -> None:
        with self._lock:
            if transport == "ws":
                self.ws_connections_active = max(0, self.ws_connections_active + delta)
            else:
                self.sse_connections_active = max(0, self.sse_connections_active + delta)

    def inc_reconnect(self) -> None:
        with self._lock:
            self.reconnect_total += 1

    def record_replay(self, *, events_count: int, lag_ms: float) -> None:
        with self._lock:
            self.replay_requests_total += 1
            self.replay_events_returned_total += events_count
            self.replay_lag_ms_last = lag_ms

    def record_export(self, *, duration_ms: float, failed: bool = False) -> None:
        with self._lock:
            self.export_total += 1
            self.export_duration_ms_last = duration_ms
            if failed:
                self.export_failures_total += 1

    def record_worker_batch(self, *, processed: int, failures: int) -> None:
        with self._lock:
            self.worker_tasks_processed += processed
            self.worker_failures_total += failures

    def record_retention(self, *, archived: int, purged: int) -> None:
        with self._lock:
            self.retention_archived_last_run = archived
            self.retention_purged_last_run = purged

    def set_queue_backlog(self, *, pending: int, dead_letter: int) -> None:
        with self._lock:
            self.queue_backlog_pending = pending
            self.queue_backlog_dead_letter = dead_letter

    def set_realtime_counts(self, *, hot: int, archive: int) -> None:
        with self._lock:
            self.realtime_events_hot_count = hot
            self.realtime_events_archive_count = archive

    def uptime_seconds(self) -> int:
        return int((datetime.now(UTC) - self.started_at).total_seconds())

    def avg_request_ms(self) -> float:
        with self._lock:
            if self.request_total == 0:
                return 0.0
            return round(self.request_latency_sum_ms / self.request_total, 2)

    def snapshot(self) -> dict:
        with self._lock:
            avg_ms = (
                round(self.request_latency_sum_ms / self.request_total, 2)
                if self.request_total
                else 0.0
            )
            return {
                "uptime_seconds": self.uptime_seconds(),
                "api": {
                    "request_total": self.request_total,
                    "error_total": self.error_total,
                    "last_request_ms": round(self.last_request_ms, 2),
                    "avg_request_ms": avg_ms,
                    "error_rate": round(self.error_total / max(self.request_total, 1), 4),
                },
                "realtime": {
                    "ws_connections_active": self.ws_connections_active,
                    "sse_connections_active": self.sse_connections_active,
                    "reconnect_total": self.reconnect_total,
                    "replay_requests_total": self.replay_requests_total,
                    "replay_events_returned_total": self.replay_events_returned_total,
                    "replay_lag_ms_last": round(self.replay_lag_ms_last, 2),
                    "events_hot_count": self.realtime_events_hot_count,
                    "events_archive_count": self.realtime_events_archive_count,
                },
                "export": {
                    "total": self.export_total,
                    "duration_ms_last": round(self.export_duration_ms_last, 2),
                    "failures_total": self.export_failures_total,
                },
                "worker": {
                    "tasks_processed": self.worker_tasks_processed,
                    "failures_total": self.worker_failures_total,
                    "queue_backlog_pending": self.queue_backlog_pending,
                    "queue_backlog_dead_letter": self.queue_backlog_dead_letter,
                },
                "retention": {
                    "archived_last_run": self.retention_archived_last_run,
                    "purged_last_run": self.retention_purged_last_run,
                },
            }


enterprise_metrics = EnterpriseMetrics()
