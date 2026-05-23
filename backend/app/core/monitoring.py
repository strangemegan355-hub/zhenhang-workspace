from datetime import UTC, datetime
from time import perf_counter


class RuntimeMetrics:
    def __init__(self) -> None:
        self.started_at = datetime.now(UTC)
        self.request_total = 0
        self.error_total = 0
        self.last_request_ms = 0.0

    def mark_request(self, elapsed_ms: float, is_error: bool) -> None:
        self.request_total += 1
        self.last_request_ms = elapsed_ms
        if is_error:
            self.error_total += 1

    def uptime_seconds(self) -> int:
        return int((datetime.now(UTC) - self.started_at).total_seconds())


runtime_metrics = RuntimeMetrics()


def now_perf() -> float:
    return perf_counter()
