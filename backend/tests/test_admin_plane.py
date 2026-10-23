"""Admin plane: routing, permission split and privilege-escalation guards.

No database is involved. Authentication is replaced with a constructed user whose roles carry
real permission codes, so `require_permissions` runs its genuine logic, while the repository and
audit layers are monkeypatched. Coroutines are driven with `asyncio.run` so the suite depends on
no asyncio plugin configuration.
"""

from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

# Set before any app import: collection imports this module, which imports
# app.services.admin_service -> app.core.security -> app.config.settings, and Settings requires
# SECRET_KEY at instantiation. The conftest fixture runs later than collection.
os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long!!")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:5432/erp_db")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")

from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.repositories import admin_repository as repo  # noqa: E402
from app.services import admin_service as svc  # noqa: E402


def make_user(*codes: str, is_superuser: bool = False, department_id=None, user_id=None):
    """Build a user whose single role grants exactly `codes`."""
    permissions = [SimpleNamespace(code=code) for code in codes]
    role = SimpleNamespace(
        id=uuid4(), code="probe_role", name="Probe", data_scope="self", permissions=permissions
    )
    return SimpleNamespace(
        id=user_id or uuid4(),
        username="probe",
        email=None,
        full_name=None,
        phone=None,
        is_active=True,
        is_superuser=is_superuser,
        department_id=department_id,
        tenant_id=None,
        hashed_password="not-a-real-hash",
        roles=[role],
    )


def client_for(user):
    from app.core.deps import get_current_active_user
    from app.db.session import get_db
    from app.main import app

    async def _fake_user():
        return user

    async def _fake_db():
        yield object()

    app.dependency_overrides[get_current_active_user] = _fake_user
    app.dependency_overrides[get_db] = _fake_db
    return app, TestClient(app)


def test_admin_routes_are_registered():
    from app.main import app

    paths = {route.path for route in app.routes if hasattr(route, "path")}
    expected = {
        "/api/v1/roles",
        "/api/v1/roles/{role_id}",
        "/api/v1/roles/{role_id}/permissions",
        "/api/v1/permissions",
        "/api/v1/departments",
        "/api/v1/departments/{department_id}",
        "/api/v1/tenants",
        "/api/v1/tenants/{tenant_id}",
        "/api/v1/users",
        "/api/v1/users/{user_id}",
        "/api/v1/users/{user_id}/roles",
        "/api/v1/users/me",
        "/api/v1/users/rbac-demo",
    }
    assert expected <= paths


def test_self_service_routes_are_not_shadowed_by_the_dynamic_segment():
    """`/me` must stay reachable now that `/{user_id}` exists."""
    user = make_user()
    app, client = client_for(user)
    try:
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 200
        # UnifiedResponseMiddleware wraps every JSON body as {code, message, data}.
        payload = resp.json()["data"]
        assert payload["username"] == "probe"
        assert payload["permissions"] == []
    finally:
        app.dependency_overrides.clear()


def test_role_list_requires_its_permission():
    user = make_user("system:user:read")
    app, client = client_for(user)
    try:
        assert client.get("/api/v1/roles").status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_role_list_allows_a_holder(monkeypatch):
    from app.schemas.common import PageResponse

    async def _fake_list_roles(db, page, page_size, q):
        return PageResponse(total=0, page=1, page_size=50, items=[])

    monkeypatch.setattr(svc, "list_roles", _fake_list_roles)
    user = make_user("system:role:read")
    app, client = client_for(user)
    try:
        resp = client.get("/api/v1/roles")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 0
    finally:
        app.dependency_overrides.clear()


def test_creating_a_user_needs_the_create_code_not_the_read_code():
    user = make_user("system:user:read")
    app, client = client_for(user)
    try:
        resp = client.post(
            "/api/v1/users",
            json={"username": "newbie", "password": "Str0ngPassw0rd"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_permission_catalogue_is_read_only_over_the_api():
    """No write verb exists on the catalogue itself: codes enter through seeding only.

    Scoped to the catalogue path exactly. `/api/v1/roles/{role_id}/permissions` is a
    deliberate PUT that edits a role's permission set, not the catalogue.
    """
    from app.main import app

    catalogue_writes = [
        route.path
        for route in app.routes
        if getattr(route, "methods", None)
        and getattr(route, "path", "") == "/api/v1/permissions"
        and route.methods & {"POST", "PUT", "PATCH", "DELETE"}
    ]
    assert catalogue_writes == []


# ------------------------------------------------------------------ escalation guards


def _patch_role_and_audit(monkeypatch, role, permissions):
    async def _get_role(db, role_id):
        return role

    async def _get_permissions_by_codes(db, codes):
        return [p for p in permissions if p.code in set(codes)]

    async def _save(db, instance, load_options=()):
        return instance

    async def _noop_audit(*args, **kwargs):
        return None

    monkeypatch.setattr(repo, "get_role", _get_role)
    monkeypatch.setattr(repo, "get_permissions_by_codes", _get_permissions_by_codes)
    monkeypatch.setattr(repo, "save", _save)
    monkeypatch.setattr(svc, "write_audit_log", _noop_audit)


def test_a_delegated_admin_cannot_grant_permissions_it_does_not_hold(monkeypatch):
    role = SimpleNamespace(
        id=uuid4(), code="ops", name="Ops", description=None, is_system=False,
        data_scope="self", permissions=[],
    )
    permissions = [
        SimpleNamespace(code="master:unit:read"),
        SimpleNamespace(code="system:role:assign"),
    ]
    _patch_role_and_audit(monkeypatch, role, permissions)

    # Holds only system:role:assign, so widening the role with master:unit:read must be refused.
    delegated = make_user("system:role:assign")
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(svc.set_role_permissions(None, role.id, ["master:unit:read"], delegated))
    assert excinfo.value.status_code == 403
    assert "master:unit:read" in str(excinfo.value.detail)


def test_a_delegated_admin_may_assign_permissions_it_already_holds(monkeypatch):
    role = SimpleNamespace(
        id=uuid4(), code="ops", name="Ops", description=None, is_system=False,
        data_scope="self", permissions=[],
    )
    permissions = [SimpleNamespace(code="master:unit:read")]
    _patch_role_and_audit(monkeypatch, role, permissions)

    delegated = make_user("system:role:assign", "master:unit:read")
    result = asyncio.run(svc.set_role_permissions(None, role.id, ["master:unit:read"], delegated))
    assert result.permission_codes == ["master:unit:read"]


def test_a_system_role_cannot_be_edited_by_a_non_superuser(monkeypatch):
    role = SimpleNamespace(
        id=uuid4(), code="admin", name="Admin", description=None, is_system=True,
        data_scope="all", permissions=[],
    )
    _patch_role_and_audit(monkeypatch, role, [])

    delegated = make_user("system:role:assign", "system:role:update")
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(svc.set_role_permissions(None, role.id, [], delegated))
    assert excinfo.value.status_code == 403


def test_unknown_permission_codes_are_rejected(monkeypatch):
    role = SimpleNamespace(
        id=uuid4(), code="ops", name="Ops", description=None, is_system=False,
        data_scope="self", permissions=[],
    )
    _patch_role_and_audit(monkeypatch, role, [])

    superuser = make_user(is_superuser=True)
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(svc.set_role_permissions(None, role.id, ["not:a:code"], superuser))
    assert excinfo.value.status_code == 400


def test_a_non_superuser_cannot_assign_the_admin_role(monkeypatch):
    target = make_user(department_id=None)
    admin_role = SimpleNamespace(
        id=uuid4(), code="admin", name="Admin", is_system=True, data_scope="all", permissions=[]
    )

    async def _get_user(db, user_id):
        return target

    async def _resolve_roles(db, codes):
        return [admin_role]

    _patch_role_and_audit(monkeypatch, admin_role, [])
    monkeypatch.setattr(repo, "get_user", _get_user)
    monkeypatch.setattr(repo, "get_roles_by_codes", _resolve_roles)

    delegated = make_user("system:user:assign")
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(svc.set_user_roles(None, target.id, ["admin"], delegated))
    assert excinfo.value.status_code == 403


def test_nobody_edits_their_own_roles_without_superuser(monkeypatch):
    me = make_user("system:user:assign")
    target = make_user(user_id=me.id, department_id=None)

    async def _get_user(db, user_id):
        return target

    _patch_role_and_audit(monkeypatch, target, [])
    monkeypatch.setattr(repo, "get_user", _get_user)

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(svc.set_user_roles(None, target.id, [], me))
    assert excinfo.value.status_code == 403


def test_a_user_cannot_deactivate_themselves(monkeypatch):
    me = make_user("system:user:update")
    target = make_user(user_id=me.id, department_id=None)

    async def _get_user(db, user_id):
        return target

    _patch_role_and_audit(monkeypatch, target, [])
    monkeypatch.setattr(repo, "get_user", _get_user)

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(svc.update_user(None, target.id, {"is_active": False}, me))
    assert excinfo.value.status_code == 400


def test_listing_users_is_scoped_to_the_callers_department():
    department = uuid4()
    outsider = uuid4()
    user = make_user("system:user:read", department_id=department)

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(svc.list_users(None, 1, 50, None, outsider, user))
    assert excinfo.value.status_code == 403


# --------------------------------------------------------------- serialisation safety


def test_password_material_is_never_serialised():
    from app.schemas.user import UserAdminRead

    record = UserAdminRead.from_user(make_user("system:user:read"))
    dumped = record.model_dump()
    assert "hashed_password" not in dumped
    assert "password" not in dumped


def test_role_payload_exposes_codes_not_rows():
    from app.schemas.admin import RoleRead

    role = SimpleNamespace(
        id=uuid4(), code="ops", name="Ops", description="d", is_system=False,
        data_scope="department", permissions=[SimpleNamespace(code="b:c:d"), SimpleNamespace(code="a:b:c")],
    )
    record = RoleRead.from_role(role)
    assert record.permission_codes == ["a:b:c", "b:c:d"]
    assert "permissions" not in record.model_dump()
