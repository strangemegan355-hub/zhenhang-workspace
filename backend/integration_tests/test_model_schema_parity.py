"""Model declarations and the live schema, compared in both directions.

Round 179 proved the migration chain reproduces the live schema by running it, and round 100 measured one column
(`tenant_id`) across the tables carrying it. **Neither compares the models' declarations against `information_schema`.**
That comparison is the only falsifiable form of "模型-迁移对齐", and it fails in two distinct ways:

* **a model declares a column no migration added** — the application would break on a fresh database;
* **the database has a column no model declares** — either a migration outran the models, or something was dropped from
  a model without a migration.

Measured in round 192 against the integration database (see `MODELS_DECLARE_BUT_DB_LACKS` and `DB_HAS_BUT_MODELS_LACK`).
"""

from __future__ import annotations

import importlib
import os
import pkgutil
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from sqlalchemy import text  # noqa: E402

from app.db.session import AsyncSessionLocal  # noqa: E402

# Measured in round 192: **zero**, in both tables and columns. A model declaring a column the database lacks would break
# the application on a fresh clone, which is what the P0 unblock proved does not happen — this keeps it that way.
MODELS_DECLARE_BUT_DB_LACKS: set[str] = set()

# The eight columns the database has and no model declares, with the reason each is expected:
# * four are the `tenant_id` columns round 100 found — added by a migration while the models do not map tenants yet,
#   which is exactly the "多租户准备" state the README records;
# * four are `deleted_at`/`deleted_by` on `aftersales_service_requests` and `supplier_ledger_accounts` — soft-delete
#   columns at the database level whose models do not carry `AuditSoftDeleteMixin` (round 180 measured that only `Tenant`
#   does). **Recorded as a finding, not treated as correct**: either the models should declare the mixin and get the
#   behaviour, or the columns are leftovers.
DB_HAS_BUT_MODELS_LACK = {
    "aftersales_service_requests.deleted_at",
    "aftersales_service_requests.deleted_by",
    "customers.tenant_id",
    "machines.tenant_id",
    "quotes.tenant_id",
    "supplier_ledger_accounts.deleted_at",
    "supplier_ledger_accounts.deleted_by",
    "sys_departments.tenant_id",
}

# Alembic's own bookkeeping table is not a model.
IGNORE_TABLES = {"alembic_version"}


def _metadata_tables() -> dict[str, set[str]]:
    import app.models  # noqa: F401 - the same import `alembic/env.py` uses to register the metadata
    from app.models import Base

    for module in pkgutil.iter_modules(app.models.__path__):
        importlib.import_module(f"app.models.{module.name}")
    return {table.name: {column.name for column in table.columns} for table in Base.metadata.tables.values()}


async def _live_columns() -> dict[str, set[str]]:
    async with AsyncSessionLocal() as session:
        rows = (
            await session.execute(
                text(
                    "select table_name, column_name from information_schema.columns "
                    "where table_schema = 'public'"
                )
            )
        ).all()
    live: dict[str, set[str]] = {}
    for table_name, column_name in rows:
        live.setdefault(table_name, set()).add(column_name)
    return live


@pytest.mark.asyncio
async def test_every_column_a_model_declares_exists_in_the_database():
    declared = _metadata_tables()
    assert len(declared) >= 50, f"only {len(declared)} tables were declared, so the model import is incomplete"

    live = await _live_columns()
    offenders: list[str] = []
    for table, columns in sorted(declared.items()):
        if table not in live:
            offenders.append(f"{table} (whole table missing)")
            continue
        offenders.extend(f"{table}.{column}" for column in sorted(columns - live[table]))

    added = sorted(set(offenders) - MODELS_DECLARE_BUT_DB_LACKS)
    removed = sorted(MODELS_DECLARE_BUT_DB_LACKS - set(offenders))
    assert not added and not removed, (
        "the set of columns a model declares but the database lacks changed.\n"
        f"  new:     {added or 'none'}\n"
        f"  fixed:   {removed or 'none'}\n"
        "A new one breaks the application on a fresh database and needs a migration in the same change; a fixed one "
        "means this record is stale."
    )


@pytest.mark.asyncio
async def test_the_columns_the_database_has_undeclared_are_the_recorded_set():
    declared = _metadata_tables()
    live = await _live_columns()

    found: list[str] = []
    for table, columns in sorted(live.items()):
        if table in IGNORE_TABLES or table not in declared:
            continue
        found.extend(f"{table}.{column}" for column in sorted(columns - declared[table]))

    added = sorted(set(found) - DB_HAS_BUT_MODELS_LACK)
    removed = sorted(DB_HAS_BUT_MODELS_LACK - set(found))
    assert not added and not removed, (
        "the set of columns the database has and no model declares changed.\n"
        f"  new:     {added or 'none'}\n"
        f"  gone:    {removed or 'none'}\n"
        "A new one means a migration outran the models, or a column was dropped from a model without a migration. "
        "If it is deliberate, record the reason here."
    )
