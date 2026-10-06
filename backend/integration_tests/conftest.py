import asyncio
import os
import sys

import pytest
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# psycopg's async mode cannot run on Windows' default ProactorEventLoop ("Psycopg cannot use the
# 'ProactorEventLoop' to run in async mode"), and pytest-asyncio builds its loop before the
# application's own policy hook in app/db/session.py is imported. Setting the policy here, plus the
# event_loop_policy fixture below, is what lets these tests connect on Windows at all.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # On Python 3.14 setting the policy no longer implies that get_event_loop() creates one, and
    # pytest-asyncio needs a current loop before it can run the first async test. Without this, a
    # single file run on its own fails with "There is no current event loop in thread 'MainThread'"
    # while the full suite passes, because an earlier test happened to create the loop.
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.SelectorEventLoop())

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
