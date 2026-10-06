"""The migration chain must run in both directions.

`alembic upgrade head` had been proven — an empty database reaches 0039 with 82 tables. Nothing had ever run
it **downwards**, and it did not work: `alembic downgrade base` stopped at 0006 with

    HINT:  Use DROP ... CASCADE to drop the dependent objects too.
    [SQL: DROP TABLE approval_templates]

because that migration's hand-written `downgrade()` dropped the table eight lines before the `quotes`
constraint that referenced it. A release therefore had no rollback path, which is exactly when one is needed.

This test performs the whole round trip on a scratch database of its own, so it neither reads nor disturbs the
integration database the rest of the suite uses: create, `upgrade head`, `downgrade base` back to just
`alembic_version`, then `upgrade head` again. It is slower than the rest of the suite (the upgrade takes about
a minute), which is why it lives with the integration tests and runs in the backend CI job.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

BACKEND = Path(__file__).resolve().parents[1]

INTEGRATION_DATABASE_URL = os.getenv(
    "INTEGRATION_DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:55432/erp_db"
)
SCRATCH_DB = "erp_migration_round_trip"
os.environ.setdefault("SECRET_KEY", "integration-secret-key-32-chars-long!")


def _libpq_url(database: str) -> str:
    """The same credentials as the integration URL, pointing at another database, for psycopg itself."""
    return INTEGRATION_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://").rsplit("/", 1)[0] + "/" + database


def _alembic(database: str, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(BACKEND)
    env["DATABASE_URL"] = INTEGRATION_DATABASE_URL.rsplit("/", 1)[0] + "/" + database
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _table_count(database: str) -> int:
    with psycopg.connect(_libpq_url(database)) as conn:
        row = conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
        ).fetchone()
    return int(row[0]) if row else 0


@pytest.fixture
def scratch_database():
    try:
        with psycopg.connect(_libpq_url("postgres"), autocommit=True) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS {SCRATCH_DB}')
            conn.execute(f"CREATE DATABASE {SCRATCH_DB}")
    except Exception as exc:  # pragma: no cover - reported as a failure, not an error
        pytest.fail(f"could not create the scratch database: {exc}")

    try:
        yield SCRATCH_DB
    finally:
        try:
            with psycopg.connect(_libpq_url("postgres"), autocommit=True) as conn:
                conn.execute(f'DROP DATABASE IF EXISTS {SCRATCH_DB} WITH (FORCE)')
        except Exception:  # noqa: BLE001 - cleanup must not mask a result
            pass


def test_the_chain_runs_downwards_and_back_up(scratch_database: str):
    up = _alembic(scratch_database, "upgrade", "head")
    assert up.returncode == 0, f"upgrade failed:\n{up.stdout[-1200:]}\n{up.stderr[-1200:]}"
    at_head = _table_count(scratch_database)
    assert at_head > 50, f"expected the schema at head, found {at_head} tables"

    down = _alembic(scratch_database, "downgrade", "base")
    assert down.returncode == 0, (
        "the chain cannot be reversed, so a release has no rollback path:\n"
        f"{down.stdout[-1200:]}\n{down.stderr[-1500:]}"
    )
    remaining = _table_count(scratch_database)
    assert remaining == 1, (
        f"downgrade base left {remaining} tables; only alembic_version should remain "
        "(some downgrade() drops or creates in the wrong order)"
    )

    again = _alembic(scratch_database, "upgrade", "head")
    assert again.returncode == 0, f"forward after reverse failed:\n{again.stdout[-1200:]}"
    assert _table_count(scratch_database) == at_head, "the round trip did not restore the schema"
