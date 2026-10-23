"""Database baseline: the migration chain applied to a real PostgreSQL, and the app wired to it.

The default `tests/` suite is deliberately database-free (fakes and dependency overrides), and
`pyproject.toml` sets `testpaths = ["tests"]`, so this directory runs only when asked for. It needs
the integration stack on its own ports so it cannot clash with a development stack:

    docker compose -f integration_tests/docker-compose.integration.yml up -d
    $env:INTEGRATION_DATABASE_URL = "postgresql+psycopg://erp:erp@localhost:55432/erp_db"
    python -m alembic upgrade head
    python -m pytest integration_tests -q

`DATABASE_URL` is set from `INTEGRATION_DATABASE_URL` before anything imports `app.*`, because the
settings and the engine are built at import time.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

BACKEND = Path(__file__).resolve().parents[1]

INTEGRATION_DATABASE_URL = os.getenv(
    "INTEGRATION_DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:55432/erp_db"
)
os.environ["DATABASE_URL"] = INTEGRATION_DATABASE_URL
os.environ.setdefault("SECRET_KEY", "integration-secret-key-32-chars-long!")


def _model_tables() -> set[str]:
    tables: set[str] = set()
    for path in (BACKEND / "app" / "models").glob("*.py"):
        if path.stem in {"__init__", "base", "associations"}:
            continue
        tables |= set(re.findall(r'__tablename__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8")))
    return tables


def _head_revisions() -> set[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(BACKEND)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, f"alembic heads failed:\n{result.stderr[-1500:]}"
    return {line.split()[0] for line in result.stdout.splitlines() if line.strip()}


async def test_the_database_is_at_the_head_revision(integration_db_engine, integration_help_text):
    try:
        async with integration_db_engine.connect() as conn:
            stored = list((await conn.execute(text("SELECT version_num FROM alembic_version"))).scalars())
    except Exception as exc:  # pragma: no cover - reported as a failure, not an error
        raise AssertionError(f"PostgreSQL integration failed. {integration_help_text}") from exc

    heads = _head_revisions()
    assert len(stored) == 1, f"expected exactly one applied revision, found {stored}"
    assert stored[0] in heads, f"database is at {stored[0]}, but the chain's head is {sorted(heads)}"


async def test_every_model_table_exists_in_the_database(integration_db_engine):
    """The DDL check proves the chain emits the tables; this proves a real database has them."""
    expected = _model_tables()
    assert expected, "no model tables found"

    async with integration_db_engine.connect() as conn:
        present = set(
            (
                await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                )
            ).scalars()
        )

    missing = sorted(table for table in expected if table not in present)
    assert missing == [], (
        "these model tables are absent from the migrated database, so the schema does not match the "
        f"models: {missing}"
    )


async def test_the_readiness_probe_answers_against_the_real_stack():
    """One call proves the app, the database and Redis are wired to each other."""
    import httpx
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://integration") as client:
        response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200, response.text[:500]
    body = response.json()
    # UnifiedResponseMiddleware wraps JSON as {code, message, data}; accept either shape.
    payload = body.get("data", body) if isinstance(body, dict) else {}
    assert isinstance(payload, dict) and payload, f"unexpected readiness payload: {body!r}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
