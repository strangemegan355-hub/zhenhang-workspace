"""Round 230's empty cell: the columns the models declare versus the columns the chain creates.

Round 229 established that **two green checks can compare two different pairs**. `test_schema_model_alignment.py` compares
schemas with models; `test_migration_reproduces_live_schema.py` compares the chain with the live database. **Nothing
compared the models with the chain**, and round 229's example proved the gap is real: an `accounting_settlements` table
that migration `0026` creates and **no model declares** passes both.

This closes it by building a database from `alembic upgrade head` — the same technique the reproduction test uses — and
comparing its columns with `Base.metadata`, **in both directions**:

* a table or column the chain creates and no model declares;
* a table or column a model declares and the chain never creates.

**The pair this cannot see is chain versus live**, which is the other test's job — so a column added directly to a live
database is invisible here **by design**, and that division is the point of having both.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

SOURCE = os.getenv("INTEGRATION_DATABASE_URL") or os.getenv("DATABASE_URL")
if not SOURCE:
    pytest.skip("this test needs INTEGRATION_DATABASE_URL (or DATABASE_URL)", allow_module_level=True)

_parsed = re.match(r"postgresql(?:\+\w+)?://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:/]+):(?P<port>\d+)/", SOURCE)
assert _parsed, f"cannot read the integration URL: {SOURCE[:40]}"
USER, PASSWORD = _parsed.group("user"), _parsed.group("password")
HOST, PORT = _parsed.group("host"), _parsed.group("port")

SCRATCH_DB = "erp_model_chain_check"
PYTHON = str(BACKEND / ".venv" / "Scripts" / "python.exe")

# Tables the chain creates that no model declares, and models with no table, each with the reason it is correct. **An
# entry here is a decision; the default is that the two layers agree.**
#
# Measured in round 231 — the first run of this pair: **chain 1036 columns, models 1019, chain-only 17, model-only 0**, so
# the models are a strict subset and every mismatch is something the chain has and the models do not.
EXEMPT_TABLES: dict[str, str] = {
    "accounting_settlements": (
        "created by migration 0026 and declared by no model, and **nothing in `app/` reads it** (round 229 grepped the "
        "whole backend and found it only in the migration). **Removing it is a migration, so it is a decision rather than "
        "a fix** — exempted here with that reason so the pair is still compared and this stays visible."
    ),
}
EXEMPT_COLUMNS: dict[str, str] = {
    "alembic_version.version_num": "alembic's own bookkeeping table, which no model should declare",
    "aftersales_service_requests.deleted_at": (
        "legacy soft-delete columns predating `AuditSoftDeleteMixin`, which uses `created_by` + `is_deleted` instead. "
        "**No code reads `deleted_at` or `deleted_by` anywhere in `app/`** — dropping them is a migration, i.e. a decision."
    ),
    "aftersales_service_requests.deleted_by": "same legacy pair as `deleted_at` above; no code reads it",
    "supplier_ledger_accounts.deleted_at": "same legacy pair as the aftersales columns; no code reads it",
    "supplier_ledger_accounts.deleted_by": "same legacy pair as `deleted_at` above; no code reads it",
    "customers.tenant_id": (
        "tenant-isolation preparation: **nine tables carry `tenant_id` and only `sys_users` is stamped**, recorded as a "
        "measured boundary. These four are deliberate scaffolding awaiting the decision to enforce tenancy, not drift."
    ),
    "machines.tenant_id": "tenant-isolation scaffolding, same as `customers.tenant_id`",
    "quotes.tenant_id": "tenant-isolation scaffolding, same as `customers.tenant_id`",
    "sys_departments.tenant_id": "tenant-isolation scaffolding, same as `customers.tenant_id`",
}


def _url(database: str, driver: str = "") -> str:
    return f"postgresql{driver}://{USER}:{PASSWORD}@{HOST}:{PORT}/{database}"


def _chain_columns() -> set[tuple[str, str]]:
    """Every (table, column) a database built from the migration chain has."""
    with psycopg.connect(_url("postgres"), autocommit=True) as conn:
        conn.execute(f'drop database if exists "{SCRATCH_DB}"')
        conn.execute(f'create database "{SCRATCH_DB}"')
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
        f"alembic upgrade head failed on an empty database, so this comparison has no subject:\n"
        f"{(migration.stderr or migration.stdout)[-800:]}"
    )
    with psycopg.connect(_url(SCRATCH_DB)) as conn:
        rows = conn.execute(
            "select table_name, column_name from information_schema.columns "
            "where table_schema = 'public' order by table_name, column_name"
        ).fetchall()
    return {(table, column) for table, column in rows}


def _model_columns() -> set[tuple[str, str]]:
    """Every (table, column) the models declare, counting only `mapped_column` attributes."""
    from app.models import Base

    found: set[tuple[str, str]] = set()
    for table in Base.metadata.tables.values():
        for column in table.columns:
            found.add((table.name, column.name))
    return found


def test_the_models_and_the_migration_chain_declare_the_same_columns():
    chain = _chain_columns()
    models = _model_columns()

    # A floor from the codebase's side: a chain that produced almost nothing would mean the build failed rather than that
    # the two layers agree.
    assert len(chain) >= 400, f"the chain produced only {len(chain)} columns, so the comparison is not meaningful"

    extra_in_chain = sorted(
        f"{table}.{column}"
        for table, column in chain - models
        if table not in EXEMPT_TABLES and f"{table}.{column}" not in EXEMPT_COLUMNS
    )
    missing_from_chain = sorted(
        f"{table}.{column}" for table, column in models - chain if f"{table}.{column}" not in EXEMPT_COLUMNS
    )

    assert extra_in_chain == [], (
        "**the migration chain creates these, and no model declares them.** Either add them to the models, or remove "
        "them from the chain — **and if a table belongs to neither layer's purpose, say so in `EXEMPT_TABLES` with the "
        "reason** rather than leaving this pair uncompared:\n  " + "\n  ".join(extra_in_chain[:40])
    )
    assert missing_from_chain == [], (
        "**the models declare these and the chain never creates them**, so a fresh deployment would be missing columns "
        "the code expects:\n  " + "\n  ".join(missing_from_chain[:40])
    )


def test_the_exemptions_say_why():
    thin = [key for key, reason in {**EXEMPT_TABLES, **EXEMPT_COLUMNS}.items() if len(reason.strip()) < 20]
    assert thin == [], f"these exemptions do not say why the layers may disagree here: {thin}"
