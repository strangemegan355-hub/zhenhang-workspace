"""Pin the shape of the five admin surfaces, so "补齐" has a definition and a change is visible.

Phase 3 says 补齐 roles/permissions/departments/tenants 与用户管理 API. Rounds 159/173 proved every route's
authorization is audited and round 152 that single-object access is scoped — **but the verbs each surface offers were
never listed**, and a missing verb is invisible to an audit that only checks the routes that exist.

Measured in round 180 from the application's own route table. **What the surfaces are, and what they are not:**

* `roles` — list, item, create, update, and `PUT /{role_id}/permissions`;
* `permissions` — **one collection GET, by design**: permission codes are defined in code and provisioned by seeders,
  not authored through the API, so there is nothing to create or update;
* `departments` — list, create, update; **no item read**;
* `tenants` — list, item, create, update;
* `users` — list, item, create, update, `GET /me`, `PUT /{user_id}/roles`.

**And no surface offers DELETE, which is a model-level fact rather than an omission:** only `Tenant` carries
`AuditSoftDeleteMixin`; `Role`, `Permission`, `Department` and `User` have no `is_deleted` column at all, and
`admin_service` has no delete function for any of them. **The asymmetry worth naming is `Tenant`: it is the one model that
supports soft deletion and it has no delete route**, so the capability is declared and unused. `departments`' missing item
read is the other asymmetry.

Both are **recorded, not fixed**: adding a delete endpoint is a product decision, and this test's job is to make the
current shape explicit and to fail when it changes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


SURFACES = {
    "roles": "/api/v1/roles",
    "permissions": "/api/v1/permissions",
    "departments": "/api/v1/departments",
    "tenants": "/api/v1/tenants",
    "users": "/api/v1/users",
}

# (method, suffix) with the collection as `""` and any parameter segment as `"/{...}"` — the same normalisation
# `_shape` applies, because the first version pinned the literal `/{role_id}` and disagreed with its own reader.
EXPECTED: dict[str, set[tuple[str, str]]] = {
    "roles": {
        ("GET", ""),
        ("GET", "/{...}"),
        ("POST", ""),
        ("PUT", "/{...}"),
        ("PUT", "/{...}/permissions"),
    },
    "permissions": {("GET", "")},
    "departments": {("GET", ""), ("POST", ""), ("PUT", "/{...}")},
    "tenants": {("GET", ""), ("GET", "/{...}"), ("POST", ""), ("PUT", "/{...}")},
    "users": {
        ("GET", ""),
        ("GET", "/me"),
        ("GET", "/rbac-demo"),
        ("GET", "/{...}"),
        ("POST", ""),
        ("PUT", "/{...}"),
        ("PUT", "/{...}/roles"),
    },
}

# Where a route parameter's name differs from the suffix shape above; the test normalises `/{anything}` to `"/{...}"`.
def _shape(path: str, prefix: str) -> str:
    suffix = path[len(prefix) :]
    if not suffix:
        return ""
    # A parameter segment becomes `/{...}`; a literal segment stays, so `/me` and `/rbac-demo` are distinguishable.
    parts = ["/{...}" if part.startswith("{") else "/" + part for part in suffix.strip("/").split("/")]
    return "".join(parts)


def _actual() -> dict[str, set[tuple[str, str]]]:
    os.environ.setdefault("SECRET_KEY", "integration-baseline-secret-key-32chars")
    os.environ.setdefault(
        "DATABASE_URL", "postgresql+psycopg://unit-tests:unreachable@127.0.0.1:59999/no_such_database"
    )
    from app.main import app

    found: dict[str, set[tuple[str, str]]] = {name: set() for name in SURFACES}
    for route in app.routes:
        path = getattr(route, "path", "")
        for name, prefix in SURFACES.items():
            if path != prefix and not path.startswith(prefix + "/"):
                continue
            for method in getattr(route, "methods", []) or []:
                if method in {"HEAD", "OPTIONS"}:
                    continue
                found[name].add((method, _shape(path, prefix)))
    return found


def test_the_scan_finds_the_five_surfaces():
    actual = _actual()
    empty = sorted(name for name, routes in actual.items() if not routes)
    assert empty == [], f"these admin surfaces have no routes at all, so the scan is broken: {empty}"


def test_each_admin_surface_offers_exactly_the_pinned_routes():
    actual = _actual()
    for name, expected in EXPECTED.items():
        assert actual[name] == expected, (
            f"{name} offers {sorted(actual[name])} but the pin says {sorted(expected)}. A missing verb is the 补齐 this "
            "test exists to make visible; an extra one needs the same deliberate change."
        )


def test_no_admin_surface_deletes_and_the_models_explain_why():
    """DELETE is absent for a model-level reason, not by accident — and `Tenant` is the asymmetry."""
    actual = _actual()
    deleters = sorted(name for name, routes in actual.items() if any(method == "DELETE" for method, _ in routes))
    assert deleters == [], (
        f"these surfaces now offer DELETE: {deleters}. If that is deliberate, say why in this file — only `Tenant` "
        "carries the soft-delete mixin, so the others would be hard deletes."
    )

    import app.models.department as department_module
    import app.models.role as role_module
    import app.models.tenant as tenant_module
    import app.models.user as user_module

    def _has_soft_delete(module) -> bool:
        for value in vars(module).values():
            if isinstance(value, type) and hasattr(value, "__mapper__"):
                return any("SoftDelete" in base.__name__ for base in value.__mro__)
        return False

    assert _has_soft_delete(tenant_module), "Tenant no longer carries the soft-delete mixin, so this reason is stale"
    for module, label in ((role_module, "Role"), (department_module, "Department"), (user_module, "User")):
        assert not _has_soft_delete(module), (
            f"{label} now supports soft deletion, so a DELETE route may be the intended 补齐 — update this file and the "
            "pin above in the same change"
        )
