from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.config.settings import settings
from app.core.enterprise_metrics import enterprise_metrics
from app.db.session import get_db
from app.models.tasking import TaskQueue

router = APIRouter()


def _is_production() -> bool:
    return settings.environment == "production" or settings.app_env == "prod"


async def verify_metrics_access(
    x_metrics_api_key: Annotated[str | None, Header(alias="X-Metrics-Api-Key")] = None,
) -> None:
    if not _is_production():
        return
    if not settings.metrics_api_key:
        raise HTTPException(
            status_code=403,
            detail="Metrics endpoint is disabled in production until METRICS_API_KEY is configured",
        )
    if x_metrics_api_key != settings.metrics_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Metrics-Api-Key")


@router.get("/live", summary="Liveness probe")
async def live() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "uptime_seconds": enterprise_metrics.uptime_seconds(),
    }


@router.get("/ready", summary="Readiness probe (DB + Redis)")
async def ready(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    db_started = perf_counter()
    await db.execute(text("SELECT 1"))
    db_latency_ms = round((perf_counter() - db_started) * 1000, 2)
    from app.core.redis_client import get_redis

    redis_started = perf_counter()
    redis = await get_redis()
    await redis.ping()
    redis_latency_ms = round((perf_counter() - redis_started) * 1000, 2)
    return {
        "status": "ready",
        "service": settings.app_name,
        "version": __version__,
        "db": {"status": "up", "latency_ms": db_latency_ms},
        "redis": {"status": "up", "latency_ms": redis_latency_ms},
        "runtime": enterprise_metrics.snapshot()["api"],
    }


@router.get(
    "/metrics",
    summary="Enterprise metrics snapshot",
    dependencies=[Depends(verify_metrics_access)],
)
async def metrics(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    pending = int(
        (
            await db.execute(
                select(func.count()).select_from(TaskQueue).where(
                    TaskQueue.is_deleted.is_(False),
                    TaskQueue.status == "pending",
                    TaskQueue.dead_letter.is_(False),
                )
            )
        ).scalar_one()
    )
    dead = int(
        (
            await db.execute(
                select(func.count()).select_from(TaskQueue).where(
                    TaskQueue.is_deleted.is_(False),
                    TaskQueue.dead_letter.is_(True),
                )
            )
        ).scalar_one()
    )
    enterprise_metrics.set_queue_backlog(pending=pending, dead_letter=dead)
    try:
        from app.realtime.retention import count_hot_and_archive

        hot, archive = await count_hot_and_archive(db)
        enterprise_metrics.set_realtime_counts(hot=hot, archive=archive)
    except Exception:
        pass
    snap = enterprise_metrics.snapshot()
    snap["policy"] = {
        "realtime_hot_retention_days": settings.realtime_hot_retention_days,
        "realtime_replay_retention_days": settings.realtime_replay_retention_days,
        "realtime_archive_retention_days": settings.realtime_archive_retention_days,
    }
    return snap
