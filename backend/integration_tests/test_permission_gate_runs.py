"""The permission gate must run somewhere automated, and this is that place.

`backend/scripts/verify_permissions.py` has existed since the trial-role work and is **invoked by nothing**: it appears
in `docs/INTERNAL_TRIAL_GUIDE.md` as a manual instruction, and `backend/scripts/audit_authz.py` reads its
`FORBIDDEN_FOR_TRIAL` **as source text** rather than running it. `ci.sh` runs the audit but not this. That is the class
rounds 92, 95, 112 and 117 kept finding one instance of: **a check that exists, is documented, and is reachable from no
command anyone runs.**

Its verdict depends on the database it is pointed at — round 114 established that the development database reports six
issues because it predates the current role definitions, while the integration database passes — so the integration
suite is where it belongs, next to the trial users it checks.

Run as documented, through `sys.executable`, so this exercises the script a person would run rather than a copy of its
logic. It **skips** when the trial roles are absent, because a database without them is a legitimate state for the
other integration tests and this one cannot judge it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
SCRIPT = BACKEND / "scripts" / "verify_permissions.py"
EXPECTED = "All checks passed."


def _trial_roles_present(env: dict[str, str]) -> bool:
    """True when `sales01` exists, i.e. setup_trial_users.py has run against this database.

    Uses the model's own table and column names and a **sync** engine, so nothing here guesses a schema detail:
    `_script_utils.database_url()` returns the URL the script itself would use.
    """
    code = (
        "import sys; sys.path.insert(0, 'scripts')\n"
        "from sqlalchemy import create_engine, select\n"
        "from sqlalchemy.orm import Session\n"
        "from _script_utils import database_url\n"
        "from app.models.user import User\n"
        "engine = create_engine(database_url())\n"
        "with Session(engine) as session:\n"
        "    found = session.execute(select(User).where(User.username == 'sales01')).scalar_one_or_none()\n"
        "print('yes' if found else 'no')\n"
    )
    env = dict(env)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(BACKEND)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=BACKEND,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    out = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0 and "yes" in out


def test_the_permission_gate_passes_on_this_database():
    if not SCRIPT.exists():
        pytest.skip("scripts/verify_permissions.py is not present")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(BACKEND)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
    )
    if not _trial_roles_present(env):
        pytest.skip("the trial roles are not provisioned in this database, so the gate has nothing to judge")

    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    output = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 0, (
        "the permission gate reported problems on this database. Round 114 established that its verdict depends on "
        f"which database it is pointed at, and this one is the integration database:\n{output[-3000:]}"
    )
    assert EXPECTED in output, f"the gate exited 0 without its success line:\n{output[-2000:]}"
