"""State transitions and mutations must apply the caller's data scope, like their module's reads do.

Five modules scoped their reads and not their writes. Each fixed function is called here with a recorder in
place of its repository (which returns None, so the scoped lookup is the last thing that runs) and the
assertion is that a predicate was passed. `accounting`'s pair calls `require_accounting_enabled` first, which is
stubbed to a no-op. `config.update_config` follows its domain's owner convention instead of a predicate, so its
test asserts the refusal directly.

No database is involved: the objects are transient ORM instances and the repositories are recorders.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-32-characters")

from app.domains.config.application import config_application_service as config_svc  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import accounting_service, fieldwork_service, procurement_service, work_order_service  # noqa: E402


class _Recorder:
    def __init__(self) -> None:
        self.predicates: list[object] = []

    async def __call__(self, db, object_id, predicate=None, **kwargs):
        self.predicates.append(predicate)
        return None


def _user() -> User:
    return User(id=uuid4(), username="scope-probe", hashed_password="not-used")


CASES = [
    ("fieldwork.advance_record_status", fieldwork_service, "get_record",
     lambda s, q, u: s.advance_record_status(None, q, u)),
    ("procurement.advance_entry_status", procurement_service, "get_entry",
     lambda s, q, u: s.advance_entry_status(None, q, u)),
    ("work_order.advance_work_order_status", work_order_service, "get_work_order",
     lambda s, q, u: s.advance_work_order_status(None, q, u)),
    ("work_order.claim_work_order", work_order_service, "get_work_order",
     lambda s, q, u: s.claim_work_order(None, q, SimpleNamespace(claimed_by="probe"), u)),
    ("accounting.confirm_entry", accounting_service, "get_entry",
     lambda s, q, u: s.confirm_entry(None, q, u)),
    ("accounting.void_entry", accounting_service, "get_entry",
     lambda s, q, u: s.void_entry(None, q, u)),
]


@pytest.mark.parametrize(("name", "module", "repo_fn", "call"), CASES, ids=[c[0] for c in CASES])
@pytest.mark.asyncio
async def test_transitions_apply_the_callers_scope(monkeypatch, name, module, repo_fn, call):
    recorder = _Recorder()
    monkeypatch.setattr(module.repo, repo_fn, recorder)
    if module is accounting_service:
        # Called before the lookup and unrelated to scope; stubbed so the test stays database-free.
        async def _noop(db):
            return None

        monkeypatch.setattr(module, "require_accounting_enabled", _noop)

    with pytest.raises(HTTPException) as raised:
        await call(module, uuid4(), _user())

    assert raised.value.status_code == 404, f"{name}: an out-of-scope row must be 404"
    assert len(recorder.predicates) == 1, f"{name}: the lookup must run exactly once"
    assert recorder.predicates[0] is not None, (
        f"{name} fetched the row without the data-scope predicate, so any holder of the relevant permission "
        "could act on a record outside their scope"
    )


@pytest.mark.asyncio
async def test_config_update_refuses_a_row_outside_the_callers_owner_scope(monkeypatch):
    caller = _user()

    async def _get_config_by_id(db, config_id):
        return SimpleNamespace(id=config_id, created_by=uuid4(), key="probe")

    monkeypatch.setattr(config_svc.repo, "get_config_by_id", _get_config_by_id)

    with pytest.raises(HTTPException) as raised:
        await config_svc.update_config(None, uuid4(), {"value": "x"}, caller)

    assert raised.value.status_code == 404, "a config outside the caller's scope must be a 404"
