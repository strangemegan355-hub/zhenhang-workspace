"""Layer parity, as enforced invariants rather than a one-off audit.

Three gaps this file makes impossible to ship silently, each of which was checked by hand first:

  * an endpoint module that exists but is never mounted in the router — the route would simply not
    exist, and neither tsc nor the suite would notice;
  * a hook domain file that is never re-exported from `packages/query-hooks/src/index.ts` — the
    hooks would be unreachable from every page;
  * a model whose table the migration chain never creates — the schema would not build.

The third compiles the chain to SQL, which needs no database and takes a couple of seconds. An
earlier hand check of the same property produced a false alarm because it grepped migration source
for `create_table('x'`, which the migrations wrap across lines; the generated DDL is the authority.
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
APP = BACKEND / "app"
ENDPOINTS = APP / "api" / "v1" / "endpoints"
ROUTER = APP / "api" / "v1" / "router.py"
HOOK_INDEX = REPO / "packages" / "query-hooks" / "src" / "index.ts"
HOOK_DOMAINS = REPO / "packages" / "query-hooks" / "src" / "domains"


def test_every_endpoint_module_is_mounted():
    modules = {path.stem for path in ENDPOINTS.glob("*.py") if path.stem != "__init__"}
    assert modules, "no endpoint modules found"
    router = ROUTER.read_text(encoding="utf-8")
    # The router lists its imports one per line inside a parenthesised import block.
    mounted = set(re.findall(r"^\s{4}(\w+),", router, re.M))
    assert modules - mounted == set(), (
        "these endpoint modules exist but the router never imports them, so their routes are not "
        f"served: {sorted(modules - mounted)}"
    )


def test_every_hook_domain_is_exported():
    files = {path.stem for path in HOOK_DOMAINS.glob("*.ts")} - {"keys"}
    assert files, "no hook domain files found"
    index = HOOK_INDEX.read_text(encoding="utf-8")
    exported = set(re.findall(r'export \* from "\./domains/([\w-]+)"', index))
    assert files - exported == set(), (
        f"these hook domains are never re-exported, so no page can import them: "
        f"{sorted(files - exported)}"
    )


def test_every_model_table_is_created_by_the_chain():
    tables: set[str] = set()
    for path in (APP / "models").glob("*.py"):
        if path.stem in {"__init__", "base", "associations"}:
            continue
        tables |= set(re.findall(r'__tablename__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8")))
    assert tables, "no model tables found"

    env = dict(os.environ)
    env["PYTHONPATH"] = str(BACKEND)
    env.setdefault("SECRET_KEY", "0123456789012345678901234567890123")
    env.setdefault("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/erp")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, f"the migration chain could not be compiled:\n{result.stderr[-2000:]}"
    created = set(re.findall(r"CREATE TABLE (\w+)", result.stdout))
    missing = sorted(table for table in tables if table not in created)
    assert missing == [], (
        "these model tables are never created by any migration, so a fresh database lacks them: "
        f"{missing}"
    )
