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
    """Scoping shared data fragments it; scoping company assets blocks cross-department work.

    A file can match a shared entity's glob and still belong to a scoped module:
    `supplier_ledger_service.py` matches `*supplier*` but scopes `AccountingEntry`, an owned document, exactly as
    the scoped-module rules require. So the question is which **model** a predicate is built for, not whether the
    word appears — a file that scopes one of `SCOPED_DOCUMENTS` is judged by those rules instead of this one.
    """
    scoped_models = tuple(SCOPED_DOCUMENTS.values())
    for module in sorted(SHARED_REFERENCE_DATA | SHARED_OPERATIONAL_RECORDS):
        for path in _module_sources(module):
            text = path.read_text(encoding="utf-8")
            if any(f"scope_predicate({model}" in text for model in scoped_models):
                continue  # belongs to a scoped module; the scoped rules apply to it
            assert "scope_predicate" not in text, (
                f"{path.relative_to(BACKEND)} scopes {module}, which is declared shared; "
                "master data and company assets must stay visible across departments"
            )


def test_project_actual_costs_follow_their_project():
    """Cost lines are scoped through the parent project, never by their own author."""
    text = (BACKEND / "app/services/actual_cost_service.py").read_text(encoding="utf-8")
    assert "scope_predicate_via_parent" in text
    assert "ProjectActualCost.project_id" in text


# Direct queries of a scoped model inside a service, listed one by one. There is deliberately **no heuristic**
# here: a first attempt skipped any function that mentioned a scope helper anywhere, and `void_entry` mentions one
# — it enters through `repo.get_entry(..., predicate=scope_predicate(AccountingEntry, current_user))` — so the rule
# skipped the whole function and found **nothing**, which its own vacuity guard caught. "The function mentions
# scope" is not "this select is scoped", so every site is read and recorded instead.
#
# Each entry says why it is correct where it is:
#   accounting_service.void_entry        the entry the caller acts on is scope-checked at the door; these are the
#                                        documents it came from, reached as downstream effects of an owned entry
#   *get_dashboard_overview              builds `quote_filters` from `owner_scope_user_id(current_user)` and
#   *get_workshop_board                  passes them to every Quote aggregate it runs (round 111)
REVIEWED_DIRECT_QUERIES: set[tuple[str, str, str]] = {
    ("app/services/accounting_service.py", "void_entry", "FieldworkRecord"),
    ("app/services/accounting_service.py", "void_entry", "ProcurementEntry"),
    ("app/services/accounting_service.py", "void_entry", "Quote"),
    ("app/services/dashboard_service.py", "get_dashboard_overview", "Quote"),
    ("app/services/workshop_board_service.py", "get_workshop_board", "Quote"),
}


def direct_scoped_selects() -> set[tuple[str, str, str]]:
    """(file, enclosing function, model) for every raw select of a scoped model in `app/services`.

    Round 111's three defects hid here: `test_scope_coverage` watches repository calls that omit `predicate=`, and
    a service that skips the repository entirely is invisible to it. This lists the sites that do query directly,
    so a new one has to be looked at.
    """
    import ast

    scoped_models = tuple(SCOPED_DOCUMENTS.values())
    found: set[tuple[str, str, str]] = set()
    for path in sorted((APP / "services").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for inner in ast.walk(node):
                if not isinstance(inner, ast.Call):
                    continue
                called = inner.func
                name = (
                    called.attr
                    if isinstance(called, ast.Attribute)
                    else (called.id if isinstance(called, ast.Name) else "")
                )
                if name not in {"execute", "scalar"}:
                    continue
                segment = ast.get_source_segment(source, inner) or ""
                for model in scoped_models:
                    if re.search(rf"select(_from)?\(\s*{model}\b", segment):
                        found.add((path.relative_to(BACKEND).as_posix(), node.name, model))
    return found


def test_every_direct_query_of_a_scoped_model_is_reviewed():
    """A service that queries a scoped model itself has to be read and recorded."""
    found = direct_scoped_selects()
    # A detector that finds nothing would pass silently, so it has to reach the reviewed list. The first version of
    # this rule skipped any function mentioning a scope helper and found **zero**, which this line caught.
    assert len(found) >= len(REVIEWED_DIRECT_QUERIES), (
        f"the detector found {len(found)} direct queries of a scoped model, fewer than the {len(REVIEWED_DIRECT_QUERIES)} "
        "recorded, so it is probably broken rather than the code being clean"
    )

    new = sorted(found - REVIEWED_DIRECT_QUERIES)
    stale = sorted(REVIEWED_DIRECT_QUERIES - found)
    assert not new, (
        "these services query a scoped model directly and are not recorded. Apply a scope, or add the entry with "
        "the reason it is correct:\n" + "\n".join(f"    {entry!r}," for entry in new)
    )
    assert not stale, (
        "these recorded direct queries no longer exist, so the record is out of date:\n"
        + "\n".join(f"    {entry!r}," for entry in stale)
    )
