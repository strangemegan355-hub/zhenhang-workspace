from redis.asyncio import Redis

from app.config.settings import settings

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        # Explicit timeouts: on Windows, redis://localhost can hang on IPv6 (::1)
        # while the container only listens on IPv4 — fail fast instead of stalling probes.
        _redis = Redis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=5,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
