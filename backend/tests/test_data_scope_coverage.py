"""Which entities are scoped, which are shared, and what is still pending.

Object-level authorization is only correct when it matches the meaning of the data. Rows that
belong to someone (quotes, projects, work orders) must be scoped; shared reference data
(customers, materials, machines) must NOT be, or two salespeople in different departments would
each see a different customer list and the master data would fragment.

This module records that decision as a ledger. It fails when a module appears that nobody has
classified, so the question is always answered explicitly instead of by omission, and it fails
when someone scopes shared reference data, which would be a functional regression dressed up as
a security fix.
"""

from __future__ import annotations

import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
ENDPOINTS = APP / "api" / "v1" / "endpoints"

# Owned transactional documents: an object-level scope predicate must be applied.
SCOPED_DOCUMENTS = {
    "quotes": "Quote",
    "projects": "Project",
}

# Scoped through the older per-domain helper (owner_scope_user_id / resolve_data_scope).
LEGACY_SCOPED = {"files", "configs", "notifications"}

# Reachable only with a system:* code that no trial role may hold, so object-level scoping adds
# nothing today; users already narrows by department inside the admin service.
SUPERUSER_ONLY = {"roles", "permissions", "departments", "tenants", "users"}

# Shared reference data: deliberately global. Scoping these would split the master data.
SHARED_REFERENCE_DATA = {
    "machines", "materials", "material_categories", "suppliers", "customers", "products",
    "product_categories", "product_cost_templates", "product_price_templates", "units", "boms",
    "option_groups",
}

# Owned documents that still fetch by primary key alone. Each needs the project/quote treatment.
PENDING_MIGRATION = {
    "accounting", "procurement_entries", "work_orders", "fieldwork_records", "cost_estimates",
    "aftersales", "project_actual_costs", "installation_plans", "acceptance", "equipment_units",
}

SCOPED_SOURCES = {
    # The service builds the predicate from the caller's scope; the repository receives it and
    # applies it to the statement, so the two layers are asserted against different markers.
    "quotes": {
        "app/domains/quote/application/quote_application_service.py": "scope_predicate",
        "app/domains/quote/repositories/quote_repository.py": "predicate",
    },
    "projects": {
        "app/services/project_service.py": "scope_predicate",
        "app/repositories/project_repository.py": "predicate",
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
        | PENDING_MIGRATION
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
            assert marker in text, (
                f"{module} is declared scoped but {relative} has no {marker!r}"
            )


def test_shared_reference_data_is_not_scoped():
    """Guards against the opposite mistake: scoping master data fragments it."""
    for module in sorted(SHARED_REFERENCE_DATA):
        stems = {module, module[:-1] if module.endswith("s") else module}
        paths = set()
        for stem in stems:
            for folder in ("services", "repositories"):
                paths.update((APP / folder).glob(f"*{stem}*.py"))
        for path in sorted(paths):
            text = path.read_text(encoding="utf-8")
            assert "scope_predicate" not in text, (
                f"{path.relative_to(BACKEND)} scopes shared reference data ({module}); master data "
                "must stay visible across departments"
            )


def test_pending_migration_is_tracked():
    """A canary: when the pending set empties, move those modules into SCOPED_DOCUMENTS."""
    assert PENDING_MIGRATION, "the pending set is empty; move the modules into SCOPED_DOCUMENTS"
    assert not (PENDING_MIGRATION & set(SCOPED_DOCUMENTS)), "a module cannot be scoped and pending"
