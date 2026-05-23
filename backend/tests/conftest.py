import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _configure_test_env() -> None:
    os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long!!")
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:5432/erp_db")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

    # Settings are cached; ensure tests don't inherit a previously imported instance.
    from app.config.settings import get_settings

    get_settings.cache_clear()
