import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _configure_test_env() -> None:
    os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long!!")

    # **Deliberately unreachable, and assigned rather than `setdefault`.**
    #
    # The unit suite must not need infrastructure: `.github/workflows/ci.yml` runs it in a job with no PostgreSQL, Redis
    # or MinIO service, so a unit test that connects works locally — where a development stack is usually up — and fails
    # only in CI. The previous values pointed at the **real** local stack (`localhost:5432`, `redis://localhost:6379/0`)
    # and used `setdefault`, so even a developer's own environment could satisfy a test that should not need one.
    #
    # Measured in round 172 before changing this: the whole suite passes **208 tests** with these same unreachable
    # values, so nothing in it depends on a connection. Pointing at a closed port makes that a fact of the suite rather
    # than a property of whoever runs it.
    os.environ["DATABASE_URL"] = "postgresql+psycopg://unit-tests:unreachable@127.0.0.1:59999/no_such_database"
    os.environ["REDIS_URL"] = "redis://127.0.0.1:59998/0"
    os.environ["MINIO_ENDPOINT"] = "127.0.0.1:59997"

    # Settings are cached; ensure tests don't inherit a previously imported instance.
    from app.config.settings import get_settings

    get_settings.cache_clear()
