"""The tenant boundary, pinned to what was measured — because half-isolation can arrive silently.

Round 100 measured this and the repository's own documentation agreed with it, so nothing here is a defect
being exposed: `docs/ENTERPRISE_DEPLOYMENT.md` calls it 多租户准备 (multi-tenant *preparation*), and
`app/models/tenant.py`'s docstring says "Multi-tenant foundation — single default tenant in current
deployments". Both are accurate.

What was missing is a guard. Today:

* **nine** tables carry a `tenant_id` column out of roughly eighty — `customers`, `machines`,
  `mes_equipment_signals`, `mes_oee_snapshots`, `quotes`, `realtime_events`, `realtime_events_archive`,
  `sys_departments`, `sys_users`;
* **only `sys_users` is stamped** — every business row's `tenant_id` is NULL;
* the **only** query that filters on it is `app/realtime/store.py`, and its predicate is
  `tenant_id = :tenant OR tenant_id IS NULL`, so with every row NULL it currently admits everything.

That combination is coherent as a foundation and misleading as an isolation story, and the dangerous direction is
the silent one: if a write path starts stamping `quotes` tomorrow, nothing forces the read paths to filter on it,
and the result would be a table that looks tenant-scoped and is not. This test fails either way — when the column
set changes, and when the populated set changes — so that decision has to be made deliberately.

It runs against a database because only the database can answer these questions; an earlier grep-based attempt
concluded the domain carried no tenant column at all, which was wrong.
"""

from __future__ import annotations

import os

import psycopg
import pytest

DATABASE_URL = os.getenv("INTEGRATION_DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:55432/erp_db")
# psycopg wants a libpq URL, not SQLAlchemy's driver-qualified one.
LIBPQ_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

# Measured in round 100, identical in the development and integration databases. A change here is a decision,
# not a detail: see the module docstring for why the read side has to be reconsidered at the same time.
TABLES_CARRYING_TENANT_ID = {
    "customers",
    "machines",
    "mes_equipment_signals",
    "mes_oee_snapshots",
    "quotes",
    "realtime_events",
    "realtime_events_archive",
    "sys_departments",
    "sys_users",
}
# And of those, the ones that actually hold a tenant. All business tables are NULL today.
TABLES_WITH_A_TENANT_SET = {"sys_users"}


def _query(sql: str) -> list[tuple]:
    with psycopg.connect(LIBPQ_URL) as conn:
        return conn.execute(sql).fetchall()


@pytest.fixture(scope="module")
def carrying() -> set[str]:
    rows = _query(
        "select table_name from information_schema.columns "
        "where column_name = 'tenant_id' and table_schema = 'public'"
    )
    return {row[0] for row in rows}


def test_the_tables_carrying_a_tenant_id_are_the_measured_set(carrying: set[str]) -> None:
    # A vacuity guard: a filter that silently matched nothing would make both verdicts below meaningless.
    assert len(carrying) >= 5, f"expected several tables with a tenant_id column, found {sorted(carrying)}"

    added = sorted(carrying - TABLES_CARRYING_TENANT_ID)
    removed = sorted(TABLES_CARRYING_TENANT_ID - carrying)
    assert not added and not removed, (
        "the set of tables carrying tenant_id changed, which is a decision rather than a detail.\n"
        f"  added:   {added or 'none'}\n"
        f"  removed: {removed or 'none'}\n"
        "If a business table is now tenant-scoped, its read paths must filter on it in the same change; the "
        "realtime store's predicate admits NULL rows, so a partially stamped table is not isolated."
    )


def test_only_the_users_table_actually_holds_a_tenant(carrying: set[str]) -> None:
    populated = set()
    for table in sorted(carrying):
        count = _query(f'select count(*) from "{table}" where tenant_id is not null')[0][0]
        if count:
            populated.add(table)

    assert populated >= TABLES_WITH_A_TENANT_SET, (
        f"at least {sorted(TABLES_WITH_A_TENANT_SET)} should hold a tenant, but only {sorted(populated)} do; "
        "the seeding that attaches users to the tenant may have stopped running"
    )
    assert populated == TABLES_WITH_A_TENANT_SET, (
        "these tables now hold a tenant but the boundary recorded in this file says they do not, so either "
        "update the record or finish the isolation — every read path for them must filter too:\n"
        f"  newly populated: {sorted(populated - TABLES_WITH_A_TENANT_SET)}"
    )
