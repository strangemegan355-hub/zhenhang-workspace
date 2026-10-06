"""Two work-order project lookups and a procurement batch must respect the caller's scope.

`_ensure_project` only checked existence, so a work order could be created against another department's project;
`_maybe_set_manufacturing` *mutates* the project and had the same gap, so a caller could change another
department's stage. The legacy `project_repository.get_project` already took a `predicate`.

`transfer_arrived_to_actual_cost` receives a user and listed every arrived entry through a repository function
that accepted no predicate. Its caller is the `POST /transfer-arrived` route, not background work, so the batch
is scoped like every other read in that module and the repository grew the parameter its siblings have.

Pinned with recorders and no database. Each recorder returns nothing so the service stops at the lookup.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-32-characters")

from app.models.user import User  # noqa: E402
from app.services import procurement_service, work_order_service  # noqa: E402


class _Recorder:
    def __init__(self, value=None) -> None:
        self.value = value
        self.predicates: list[object] = []

    async def __call__(self, db, object_id=None, predicate=None, **kwargs):
        self.predicates.append(predicate)
        return self.value


def _user() -> User:
    return User(id=uuid4(), username="scope-probe", hashed_password="not-used")


@pytest.mark.asyncio
async def test_ensure_project_refuses_an_out_of_scope_project(monkeypatch):
    recorder = _Recorder(None)
    monkeypatch.setattr(work_order_service.project_repo, "get_project", recorder)

    with pytest.raises(HTTPException) as raised:
        await work_order_service._ensure_project(None, uuid4(), _user())

    assert raised.value.status_code == 404
    assert recorder.predicates and recorder.predicates[0] is not None, (
        "_ensure_project looked the project up without the data-scope predicate, so a work order could be "
        "created against another department's project"
    )


@pytest.mark.asyncio
async def test_setting_manufacturing_refuses_an_out_of_scope_project(monkeypatch):
    recorder = _Recorder(None)
    monkeypatch.setattr(work_order_service.project_repo, "get_project", recorder)

    await work_order_service._maybe_set_manufacturing(None, uuid4(), _user())

    assert recorder.predicates and recorder.predicates[0] is not None, (
        "_maybe_set_manufacturing looked the project up without the data-scope predicate, so it could change "
        "another department's project stage"
    )


@pytest.mark.asyncio
async def test_the_transfer_batch_is_scoped(monkeypatch):
    recorder = _Recorder([])
    monkeypatch.setattr(procurement_service.repo, "list_arrived_not_transferred", recorder)

    # The service commits once after the loop, so the session needs that one method; nothing else is touched
    # because the recorder returns no entries.
    class _Session:
        async def commit(self):
            return None

    result = await procurement_service.transfer_arrived_to_actual_cost(_Session(), _user())

    assert recorder.predicates and recorder.predicates[0] is not None, (
        "transfer_arrived_to_actual_cost listed arrived entries without the data-scope predicate, so it "
        "transferred records from every department"
    )
    assert result.transferred_count == 0
