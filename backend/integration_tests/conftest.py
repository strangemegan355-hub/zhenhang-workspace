import os

import pytest
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

INTEGRATION_DATABASE_URL = os.getenv(
    "INTEGRATION_DATABASE_URL",
    "postgresql+psycopg://erp:erp@localhost:55432/erp_db",
)
INTEGRATION_REDIS_URL = os.getenv("INTEGRATION_REDIS_URL", "redis://localhost:56379/0")


@pytest.fixture
async def integration_db_engine():
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def integration_redis():
    client = Redis.from_url(INTEGRATION_REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
def integration_help_text() -> str:
    return (
        "Start services first: "
        "docker compose -f integration_tests/docker-compose.integration.yml up -d"
    )
