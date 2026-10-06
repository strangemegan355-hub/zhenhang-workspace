"""The trial-delivery importer, exercised against the samples the guide tells operators to use.

`docs/INTERNAL_TRIAL_GUIDE.md` step 3 is `python scripts/import_initial_master_data.py --dir data/import_samples`
and the shipped samples live at `backend/data/import_samples/`, which is exactly what that path means when the
documented working directory is `backend/`. Nothing had ever run it.

The dry run is what makes this safe to test: it parses every file and reports what it would do, writing
nothing. Both halves are pinned here — the report covers the shipped samples, and the database is unchanged
afterwards, which is the property an operator relies on when they run it before a delivery.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import func, select

BACKEND = Path(__file__).resolve().parents[1]

os.environ["DATABASE_URL"] = os.getenv(
    "INTEGRATION_DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:55432/erp_db"
)
os.environ.setdefault("SECRET_KEY", "integration-secret-key-32-chars-long!")

SAMPLES = BACKEND / "data" / "import_samples"

EXPECTED = (
    "would create customer CUST-001",
    "would create machine MCH-001",
    "would create BOM MCH-001/V1.0",
    "would create item M01-001 on MCH-001/V1.0",
)


def _dry_run() -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(BACKEND)
    return subprocess.run(
        [
            sys.executable,
            "scripts/import_initial_master_data.py",
            "--dir",
            "data/import_samples",
            "--dry-run",
        ],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_the_shipped_samples_are_present():
    for name in ("customers.csv", "machines.csv", "boms.csv", "bom_items.csv", "users.csv"):
        assert (SAMPLES / name).exists(), f"the guide tells operators to import {name}, which is not shipped"


def test_the_dry_run_reports_what_it_would_create():
    result = _dry_run()
    assert result.returncode == 0, f"{result.stdout[-1200:]}\n{result.stderr[-800:]}"
    for marker in EXPECTED:
        assert marker in result.stdout, f"the dry run no longer reports {marker!r}:\n{result.stdout[-1200:]}"
    # A seeded trial environment skips existing users; a fresh one would create them.
    assert ("skip: user sales01 already exists" in result.stdout) or (
        "would create user sales01" in result.stdout
    )


async def test_the_dry_run_writes_nothing(integration_db_engine):
    from app.models.customer import Customer

    async def count() -> int:
        async with integration_db_engine.connect() as conn:
            return int((await conn.execute(select(func.count()).select_from(Customer))).scalar_one())

    before = await count()
    result = _dry_run()
    assert result.returncode == 0, result.stderr[-800:]
    after = await count()
    assert before == after, (
        f"the dry run changed the customer table from {before} to {after} rows; an operator runs it "
        "precisely because it is not supposed to write"
    )


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
