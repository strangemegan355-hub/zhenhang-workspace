"""Which entities are scoped, which are shared, and why.

Object-level authorization is only correct when it matches the meaning of the data. This module
records that decision as a ledger and fails when a module exposing object-id routes is in no set,
so the question is always answered explicitly instead of by omission. It also fails when a module
is scoped that should not be, which is how a security fix silently becomes a functional
regression.

Four categories, in order of how much reasoning they need:

* SCOPED_DOCUMENTS — rows that belong to somebody: quotes, projects, accounting entries, work
  orders, procurement entries, fieldwork records, cost estimates, service requests and project
  actual costs. A scope predicate must be applied.
* SHARED_REFERENCE_DATA — master data every department works from. Scoping it would give each
  department its own customer and material list.
* SHARED_OPERATIONAL_RECORDS — company assets and the records written against them (equipment
  units, installation plans, acceptance records). Installation, acceptance and after-sales staff
  routinely work on an asset another department registered, so scoping by creator would block the
  work rather than protect anything. These stay visible to any holder of the module's permission.
* SUPERUSER_ONLY — reachable only with a system:* code no trial role may hold.
"""

from __future__ import annotations

import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
ENDPOINTS = APP / "api" / "v1" / "endpoints"

SCOPED_DOCUMENTS = {
    "accounting": "AccountingEntry",
    "aftersales": "AfterSalesServiceRequest",
    "cost_estimates": "CostEstimate",
    "fieldwork_records": "FieldworkRecord",
    "procurement_entries": "ProcurementEntry",
    "project_actual_costs": "ProjectActualCost",
    "projects": "Project",
    "quotes": "Quote",
    "work_orders": "WorkOrder",
}

# Scoped through the older per-domain helper (owner_scope_user_id / resolve_data_scope).
LEGACY_SCOPED = {"files", "configs", "notifications"}

# Reachable only with a system:* code that no trial role may hold; `users` additionally narrows by
# department inside the admin service.
SUPERUSER_ONLY = {"roles", "permissions", "departments", "tenants", "users"}

SHARED_REFERENCE_DATA = {
    "machines", "materials", "material_categories", "suppliers", "customers", "products",
    "product_categories", "product_cost_templates", "product_price_templates", "units", "boms",
    "option_groups",
}

SHARED_OPERATIONAL_RECORDS = {
    "acceptance", "equipment_units", "installation_plans",
}

# A module is scoped when its service builds the predicate and its repository applies it, so the
# two layers are asserted against different markers.
SCOPED_SOURCES = {
    "quotes": {
        "app/domains/quote/application/quote_application_service.py": "scope_predicate",
        "app/domains/quote/repositories/quote_repository.py": "predicate",
    },
    "projects": {
        "app/services/project_service.py": "scope_predicate",
        "app/repositories/project_repository.py": "predicate",
    },
    "accounting": {
        "app/services/accounting_service.py": "scope_predicate",
        "app/repositories/accounting_repository.py": "predicate",
    },
    "work_orders": {
        "app/services/work_order_service.py": "scope_predicate",
        "app/repositories/work_order_repository.py": "predicate",
    },
    "procurement_entries": {
        "app/services/procurement_service.py": "scope_predicate",
        "app/repositories/procurement_repository.py": "predicate",
    },
    "fieldwork_records": {
        "app/services/fieldwork_service.py": "scope_predicate",
        "app/repositories/fieldwork_repository.py": "predicate",
    },
    "cost_estimates": {
        "app/services/costing_service.py": "scope_predicate",
        "app/repositories/cost_estimate_repository.py": "predicate",
    },
    "aftersales": {
        "app/services/aftersales_service.py": "scope_predicate",
        "app/repositories/aftersales_repository.py": "predicate",
    },
    "project_actual_costs": {
        "app/services/actual_cost_service.py": "scope_predicate_via_parent",
        "app/repositories/project_actual_cost_repository.py": "predicate",
    },
}

ID_ROUTE = re.compile(r'@router\.(get|put|patch|delete)\(\s*"[^"]*\{[a-z_]*_id\}')


def modules_with_id_routes() -> set[str]:
    found: set[str] = set()
    for path in sorted(ENDPOINTS.glob("*.py")):
        if path.name == "__init__.py":
            continue
        if ID_ROUTE.search(path.read_text(encoding="utf-8")):
            found.add(path.stem)
    return found


def classified() -> set[str]:
    return (
        set(SCOPED_DOCUMENTS)
        | LEGACY_SCOPED
        | SUPERUSER_ONLY
        | SHARED_REFERENCE_DATA
        | SHARED_OPERATIONAL_RECORDS
    )


def test_every_module_with_object_id_routes_is_classified():
    unclassified = sorted(modules_with_id_routes() - classified())
    assert unclassified == [], (
        "these modules expose object-id routes but nobody decided whether their rows are owned or "
        f"shared: {unclassified}"
    )


def test_the_classification_has_no_stale_entries():
    present = modules_with_id_routes()
    # `permissions` is superuser-only but exposes no object-id route, so it is not expected here.
    stale = sorted(classified() - present - {"permissions"})
    assert stale == [], f"classified modules that no longer expose object-id routes: {stale}"


def test_scoped_documents_apply_the_predicate():
    for module, sources in SCOPED_SOURCES.items():
        for relative, marker in sources.items():
            text = (BACKEND / relative).read_text(encoding="utf-8")
            assert marker in text, f"{module} is declared scoped but {relative} has no {marker!r}"


def _module_sources(module: str) -> list[Path]:
    stems = {module, module[:-1] if module.endswith("s") else module}
    paths: set[Path] = set()
    for stem in stems:
        for folder in ("services", "repositories"):
            paths.update((APP / folder).glob(f"*{stem}*.py"))
    return sorted(paths)


def test_shared_data_is_not_scoped_by_creator():
    """Scoping shared data fragments it; scoping company assets blocks cross-department work."""
    for module in sorted(SHARED_REFERENCE_DATA | SHARED_OPERATIONAL_RECORDS):
        for path in _module_sources(module):
            text = path.read_text(encoding="utf-8")
            assert "scope_predicate" not in text, (
                f"{path.relative_to(BACKEND)} scopes {module}, which is declared shared; "
                "master data and company assets must stay visible across departments"
            )


def test_project_actual_costs_follow_their_project():
    """Cost lines are scoped through the parent project, never by their own author."""
    text = (BACKEND / "app/services/actual_cost_service.py").read_text(encoding="utf-8")
    assert "scope_predicate_via_parent" in text
    assert "ProjectActualCost.project_id" in text
