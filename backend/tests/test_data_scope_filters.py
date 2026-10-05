"""Data scope: one predicate, four modes, asserted against compiled SQL.

No database is involved: each predicate is compiled to PostgreSQL SQL text and inspected, and the
quote service is checked to make sure it actually passes a scope predicate into the repository.
"""

from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long!!")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:5432/erp_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from sqlalchemy import select  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402

from app.core import data_scope  # noqa: E402
from app.core.data_scope import (  # noqa: E402
    DataScope,
    apply_data_scope,
    build_created_by_filter,
    scope_predicate,
)
from app.models.quote import Quote  # noqa: E402


def make_user(scope: str, *, department_id=None, is_superuser: bool = False):
    role = SimpleNamespace(code="probe", data_scope=scope)
    return SimpleNamespace(
        id=uuid4(), roles=[role], is_superuser=is_superuser, department_id=department_id
    )


def compiled(predicate) -> str:
    stmt = select(Quote.id).where(predicate)
    return str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_all_scope_adds_no_restriction():
    sql = compiled(scope_predicate(Quote, make_user(DataScope.ALL)))
    assert "created_by" not in sql
    assert "true" in sql.lower()


def test_superuser_is_unrestricted():
    sql = compiled(scope_predicate(Quote, make_user(DataScope.SELF, is_superuser=True)))
    assert "created_by" not in sql


def test_self_scope_filters_on_the_creator():
    user = make_user(DataScope.SELF)
    sql = compiled(scope_predicate(Quote, user))
    assert "quotes.created_by" in sql
    assert str(user.id) in sql


def test_department_scope_uses_a_users_subquery():
    department_id = uuid4()
    sql = compiled(
        scope_predicate(Quote, make_user(DataScope.DEPARTMENT, department_id=department_id))
    )
    assert "quotes.created_by IN" in sql
    assert "sys_users.department_id" in sql
    assert str(department_id) in sql


def test_department_scope_without_a_department_falls_back_to_own_rows():
    """Never widen to everything just because the account has no department."""
    user = make_user(DataScope.DEPARTMENT, department_id=None)
    sql = compiled(scope_predicate(Quote, user))
    assert "sys_users.department_id" not in sql
    assert "quotes.created_by" in sql
    assert str(user.id) in sql


def test_none_scope_denies_everything(monkeypatch):
    monkeypatch.setattr(data_scope, "resolve_data_scope", lambda user: DataScope.NONE)
    sql = compiled(scope_predicate(Quote, make_user(DataScope.NONE)))
    assert "false" in sql.lower()


def test_apply_data_scope_appends_the_predicate():
    user = make_user(DataScope.SELF)
    stmt = apply_data_scope(select(Quote.id), Quote, user)
    sql = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "quotes.created_by" in sql
    assert str(user.id) in sql


def test_legacy_helper_no_longer_treats_department_as_unrestricted():
    """The audit list went through this helper; DEPARTMENT must still narrow there."""
    department_id = uuid4()
    predicate = build_created_by_filter(
        Quote, make_user(DataScope.DEPARTMENT, department_id=department_id)
    )
    sql = compiled(predicate)
    assert "quotes.is_deleted IS false" in sql
    assert "sys_users.department_id" in sql


def test_quote_list_pushes_the_scope_into_sql(monkeypatch):
    from app.domains.quote.application import quote_application_service as svc
    from app.domains.quote.repositories import quote_repository as quote_repo

    captured: dict = {}

    async def fake_list_quotes(db, *, page, page_size, q, predicate=None, quote_kind=None):
        captured["predicate"] = predicate
        return 0, []

    monkeypatch.setattr(quote_repo, "list_quotes", fake_list_quotes)
    asyncio.run(
        svc.list_quotes(None, page=1, page_size=20, q=None, current_user=make_user(DataScope.SELF))
    )
    assert captured["predicate"] is not None
    assert "quotes.created_by" in compiled(captured["predicate"])


def test_quote_detail_fetches_through_the_scope(monkeypatch):
    """An out-of-scope quote must look absent, not forbidden: 404 leaks nothing."""
    from fastapi import HTTPException

    from app.domains.quote.application import quote_application_service as svc
    from app.domains.quote.repositories import quote_repository as quote_repo

    captured: dict = {}

    async def fake_get_quote(db, quote_id, predicate=None):
        captured["predicate"] = predicate
        return None

    monkeypatch.setattr(quote_repo, "get_quote", fake_get_quote)
    user = make_user(DataScope.DEPARTMENT, department_id=uuid4())
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(svc.get_quote_detail(None, uuid4(), user))
    assert excinfo.value.status_code == 404
    assert captured["predicate"] is not None
    assert "sys_users.department_id" in compiled(captured["predicate"])


def _parent_sql(predicate, child) -> str:
    stmt = select(child.id).where(predicate)
    return str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_parent_scope_follows_the_project():
    """An actual cost is visible exactly when its project is, not when its author is."""
    from app.core.data_scope import scope_predicate_via_parent
    from app.models.project import Project
    from app.models.project_actual_cost import ProjectActualCost

    user = make_user(DataScope.SELF)
    predicate = scope_predicate_via_parent(
        ProjectActualCost, Project, ProjectActualCost.project_id, user
    )
    sql = _parent_sql(predicate, ProjectActualCost)
    assert "project_actual_costs.project_id IN" in sql
    assert "projects.created_by" in sql
    assert str(user.id) in sql


def test_parent_scope_is_unrestricted_for_an_all_scope_role():
    from app.core.data_scope import scope_predicate_via_parent
    from app.models.project import Project
    from app.models.project_actual_cost import ProjectActualCost

    predicate = scope_predicate_via_parent(
        ProjectActualCost, Project, ProjectActualCost.project_id, make_user(DataScope.ALL)
    )
    sql = _parent_sql(predicate, ProjectActualCost)
    assert "projects" in sql
    assert "created_by" not in sql
