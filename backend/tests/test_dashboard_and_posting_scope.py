"""Three more scope-less reads: the dashboard's profit aggregate and two posting references.

`project_service.aggregate_profit_kpis` listed every project with no predicate, and its only caller — the
dashboard — held `current_user` and did not pass it, so the profit figures shown there covered every department.

`accounting_service.post_work_order_expense` and `post_cost_estimate_expense` already received `current_user`
and then looked the referenced work order / estimate up by id with no predicate, so an expense could be posted
against another department's record.

Each is pinned here with a recorder and no database. The accounting functions import their repositories inside
the function body, so the recorder is installed on the repository module itself, which is what the deferred
import resolves at call time.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-32-characters")

from app.models.user import User  # noqa: E402
from app.repositories import cost_estimate_repository, work_order_repository  # noqa: E402
from app.services import accounting_service, project_service  # noqa: E402


class _Recorder:
    def __init__(self) -> None:
        self.predicates: list[object] = []


def _user() -> User:
    return User(id=uuid4(), username="scope-probe", hashed_password="not-used")


@pytest.mark.asyncio
async def test_the_profit_aggregate_is_scoped(monkeypatch):
    recorder = _Recorder()

    async def _list_projects(db, page, page_size, q, predicate=None):
        recorder.predicates.append(predicate)
        return 0, []

    monkeypatch.setattr(project_service.repo, "list_projects", _list_projects)

    result = await project_service.aggregate_profit_kpis(None, _user())

    assert recorder.predicates and recorder.predicates[0] is not None, (
        "aggregate_profit_kpis listed projects without the data-scope predicate, so the dashboard's profit "
        "figures covered every department"
    )
    assert isinstance(result, dict)


@pytest.mark.parametrize(
    ("name", "module", "repo_fn", "service"),
    [
        ("post_work_order_expense", work_order_repository, "get_work_order", accounting_service.post_work_order_expense),
        ("post_cost_estimate_expense", cost_estimate_repository, "get_cost_estimate", accounting_service.post_cost_estimate_expense),
    ],
    ids=["work_order", "cost_estimate"],
)
@pytest.mark.asyncio
async def test_posting_scopes_the_reference(monkeypatch, name, module, repo_fn, service):
    recorder = _Recorder()

    async def _get(db, object_id, predicate=None):
        recorder.predicates.append(predicate)
        return None  # the 404 path, so nothing past the reference check runs

    monkeypatch.setattr(module, repo_fn, _get)

    class _Payload:
        amount = 1
        title = "probe"
        remark = None

    with pytest.raises(HTTPException) as raised:
        await service(None, uuid4(), _Payload(), _user())

    assert raised.value.status_code == 404, f"{name}: a missing or out-of-scope reference must be 404"
    assert recorder.predicates and recorder.predicates[0] is not None, (
        f"{name} looked the reference up without the data-scope predicate, so an expense could be posted "
        "against another department's record"
    )
