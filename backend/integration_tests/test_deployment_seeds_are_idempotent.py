"""The two seeding scripts the API runs on every start must be safe to run again.

`docker-compose.prod.yml` starts the API with
`alembic upgrade head && python scripts/bootstrap_admin.py && python scripts/seed_workflows.py`, so **both run on every
container start** against a database that already holds their output. Round 154 measured `seed_tenant.py` and
`setup_trial_users.py`; these two were never measured, and a script that is not idempotent corrupts or duplicates data
on every restart.

Measured before writing this: both exit 0 when re-run and both say what they did — `bootstrap_admin.py` prints
"admin admin already exists; the supplied password was not applied" (**it refuses to silently reset the password**, which
is the right behaviour) and `seed_workflows.py` prints `{'states_created': 0, 'transitions_created': 0}`.

**The assertion is relative on purpose.** It snapshots the counts **after the first run** and requires the **second** run
to change nothing, because a first run against an empty database legitimately creates the admin and the workflow rows. It
also avoids absolute numbers, since the integration database's contents move as other tests seed and tear down.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"

# The two the production command runs, in the order it runs them.
SCRIPTS = ("scripts/bootstrap_admin.py", "scripts/seed_workflows.py")

COUNTED_TABLES = ("sys_users", "workflow_states", "workflow_transitions", "sys_roles", "sys_permissions")


def _run(script: str) -> tuple[int, str]:
    env = dict(os.environ)
    env.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "integration-bootstrap-pw")
    # Scripts import `app.*`; compose sets PYTHONPATH, but local pytest cwd alone is not enough.
    env["PYTHONPATH"] = os.pathsep.join(
        [str(BACKEND)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
    )
    result = subprocess.run(
        [str(PYTHON), script],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    return result.returncode, ((result.stdout or "") + (result.stderr or "")).strip()


def _counts() -> dict[str, int]:
    import psycopg

    url = os.getenv("INTEGRATION_DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:55432/erp_db")
    libpq = url.replace("postgresql+psycopg://", "postgresql://")
    counts: dict[str, int] = {}
    with psycopg.connect(libpq) as conn:
        for table in COUNTED_TABLES:
            counts[table] = conn.execute(f'select count(*) from "{table}"').fetchone()[0]
    return counts


@pytest.mark.parametrize("script", SCRIPTS)
def test_running_a_deployment_seed_script_twice_changes_nothing(script: str):
    """The first run may create rows on an empty database; the second must not touch anything."""
    first_code, first_output = _run(script)
    assert first_code == 0, f"{script} failed on its first run:\n{first_output[-1500:]}"

    after_first = _counts()

    second_code, second_output = _run(script)
    assert second_code == 0, (
        f"{script} failed when run a second time, which is what the API does on every start:\n{second_output[-1500:]}"
    )

    after_second = _counts()
    changed = {table: (after_first[table], after_second[table]) for table in after_first if after_first[table] != after_second[table]}
    assert changed == {}, (
        f"re-running {script} changed the database, so every API restart would: {changed}\n{second_output[-800:]}"
    )
