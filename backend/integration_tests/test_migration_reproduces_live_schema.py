"""`alembic upgrade head` must reproduce the schema the live database actually has.

`test_migration_round_trip.py` proves an empty database reaches revision 0039 with 82 tables and that the
downgrade works. Neither it nor anything else checked whether that schema **is the same schema** the running
database carries. A migration edited by hand, a column added directly to production, an index built only there —
each would leave the repository unable to rebuild the database it runs against, and nothing would say so until a
fresh deployment behaved differently.

Method: create an empty database in the same server, run `alembic upgrade head` against it, and compare
column-level, index-level and constraint-level catalog rows with the live database. Catalog queries rather than a
`pg_dump --schema-only` diff, because they are order-independent and carry no database-name or comment noise.
The scratch database is dropped either way.

**The measurement that mattered here was of the check itself.** The first version compared constraint names
literally and reported `DIVERGED` with fourteen hundred differences — every one of them PostgreSQL's
auto-generated CHECK and NOT NULL names, which embed the owning table's OID (`2200_136104_1_not_null`). Two
databases built from the same migrations still have different OIDs, so those names differ for reasons that mean
nothing. Normalising the OID-bearing part turned 1398 differences into zero. **Read what a differing row actually
is before believing the verdict** — this repository has now produced three false alarms that way.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import psycopg

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
PYTHON = sys.executable

# No credential literal and no default: the connection details come from the URL the integration suite already
# sets, and their absence is fatal rather than a skip. The first version of this file gave a password lookup a
# literal fallback and `test_no_default_credentials.py` caught it, which is exactly the rule that guard enforces —
# a fallback in a test file is still a credential in the repository. **Describing that mistake rather than quoting
# it**, because the guard scans text: the comment that quoted the offending call was itself flagged on the next
# run, which is the same lesson as the secret gate's positive control — a repository scanner finds its own
# fixtures, so the fixture is what has to change.
_SOURCE_URL = os.getenv("INTEGRATION_DATABASE_URL") or os.getenv("DATABASE_URL")
if not _SOURCE_URL:
    raise RuntimeError(
        "this test needs INTEGRATION_DATABASE_URL (or DATABASE_URL) to know which PostgreSQL server to use; "
        "run it through the integration suite's environment rather than skipping it"
    )
_PARTS = psycopg.conninfo.conninfo_to_dict(_SOURCE_URL.replace("postgresql+psycopg://", "postgresql://"))
HOST = _PARTS.get("host", "")
PORT = int(_PARTS.get("port", "5432"))
USER = _PARTS.get("user", "")
PASSWORD = _PARTS.get("password", "")
LIVE_DB = _PARTS.get("dbname", "")
SCRATCH_DB = "erp_migration_check"

COLUMNS_SQL = """
select table_name, column_name, data_type, is_nullable, coalesce(column_default, '')
from information_schema.columns where table_schema = 'public'
order by table_name, column_name
"""
INDEXES_SQL = """
select tablename, indexname, indexdef from pg_indexes where schemaname = 'public'
order by tablename, indexname
"""
CONSTRAINTS_SQL = """
select table_name, constraint_type, constraint_name from information_schema.table_constraints
where table_schema = 'public'
order by table_name, constraint_type, constraint_name
"""
OID_IN_NAME = re.compile(r"^\d+_\d+_")


def _url(database: str, driver: str = "") -> str:
    return f"postgresql{driver}://{USER}:{PASSWORD}@{HOST}:{PORT}/{database}"


def _snapshot(database: str) -> dict[str, list[tuple]]:
    with psycopg.connect(_url(database)) as conn:
        return {
            "columns": conn.execute(COLUMNS_SQL).fetchall(),
            "indexes": conn.execute(INDEXES_SQL).fetchall(),
            # A CHECK or NOT NULL constraint that PostgreSQL named itself carries the table's OID, which differs
            # between any two databases. Stripping it is what makes the comparison meaningful.
            "constraints": [
                (table, kind, OID_IN_NAME.sub("N_N_", name) if kind == "CHECK" else name)
                for table, kind, name in conn.execute(CONSTRAINTS_SQL).fetchall()
            ],
        }


def _recreate(database: str) -> None:
    with psycopg.connect(_url("postgres"), autocommit=True) as conn:
        conn.execute(f'drop database if exists "{database}"')
        conn.execute(f'create database "{database}"')


def test_the_migration_chain_reproduces_the_live_schema():
    _recreate(SCRATCH_DB)
    try:
        environment = dict(os.environ)
        environment["DATABASE_URL"] = _url(SCRATCH_DB, "+psycopg")
        environment["PYTHONPATH"] = str(BACKEND)
        migration = subprocess.run(
            [PYTHON, "-m", "alembic", "upgrade", "head"],
            cwd=BACKEND,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert migration.returncode == 0, (
            f"alembic upgrade head failed on an empty database:\n{(migration.stderr or migration.stdout)[-1500:]}"
        )

        migrated = _snapshot(SCRATCH_DB)
        live = _snapshot(LIVE_DB)

        # A comparison over almost nothing would pass, so refuse to judge on a suspiciously small schema.
        assert len(migrated["columns"]) >= 500, (
            f"only {len(migrated['columns'])} columns were compared, which is too few to mean anything"
        )

        problems = []
        for kind in ("columns", "indexes", "constraints"):
            fresh, current = migrated[kind], live[kind]
            only_fresh = [row for row in fresh if row not in current]
            only_live = [row for row in current if row not in fresh]
            if only_fresh or only_live:
                problems.append(
                    f"{kind}: {len(fresh)} migrated vs {len(current)} live; "
                    f"only in the migrated schema: {only_fresh[:5]}; only in the live schema: {only_live[:5]}"
                )

        assert not problems, (
            "`alembic upgrade head` does not reproduce the schema this database has, so a fresh deployment "
            "would differ from the running one:\n  " + "\n  ".join(problems)
        )
    finally:
        with psycopg.connect(_url("postgres"), autocommit=True) as conn:
            conn.execute(f'drop database if exists "{SCRATCH_DB}"')
