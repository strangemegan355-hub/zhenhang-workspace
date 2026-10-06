from datetime import UTC, datetime
from time import perf_counter


def now_perf() -> float:
    return perf_counter()
