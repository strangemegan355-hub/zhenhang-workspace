"""Two invariants that no database is needed to check.

Notifications: a failed realtime push must not fail notification creation (the stored row is the
in-app delivery), and a created notification never claims an external provider it did not use.

Fieldwork summary: the counts must be restricted by the same data-scope predicate as the list.

`SECRET_KEY` is set before importing application modules, as elsewhere in this suite — collection
runs before the session fixtures.
"""

from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

os.environ.setdefault("SECRET_KEY", "0123456789012345678901234567890123")

from app.core.data_scope import DataScope


class FakeSession:
    """Just enough of AsyncSession for the notification path."""

    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0
        self.flushes = 0

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flushes += 1

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, obj: object) -> object:
        return obj


def _create(db, monkeypatch, *, push, receiver_id):
    from app.notifications import notification_service as svc

    calls: list[dict] = []

    async def fake_push(**kwargs):
        calls.append(kwargs)
        if push is not None:
            raise push
        return {}

    monkeypatch.setattr(svc, "push_notification_event", fake_push)
    obj = asyncio.run(
        svc.create_notification(
            db,
            title="测试通知",
            content="内容",
            biz_type="quote",
            biz_id=uuid4(),
            receiver_id=receiver_id,
            payload=None,
            created_by=None,
            autocommit=True,
        )
    )
    return obj, calls


def test_notification_is_delivered_by_its_own_row(monkeypatch):
    db = FakeSession()
    receiver = uuid4()
    obj, calls = _create(db, monkeypatch, push=None, receiver_id=receiver)

    assert obj.status == "sent"
    assert obj.sent_at is not None
    assert obj.channel == "inapp"
    # No external channel is implemented, so nothing may claim a provider.
    assert obj.provider_id is None
    assert len(calls) == 1, "the receiver should have been pushed to"
    assert calls[0]["user_id"] == receiver


def test_a_failed_push_does_not_lose_the_notification(monkeypatch):
    db = FakeSession()
    obj, calls = _create(db, monkeypatch, push=RuntimeError("hub down"), receiver_id=uuid4())

    assert len(calls) == 1
    # The row is the delivery: it survives a missed live update, and it still says sent.
    assert obj.status == "sent"
    assert obj.sent_at is not None


def test_no_receiver_means_no_push(monkeypatch):
    db = FakeSession()
    obj, calls = _create(db, monkeypatch, push=None, receiver_id=None)

    assert calls == []
    assert obj.status == "sent"


def test_fieldwork_summary_carries_the_callers_scope(monkeypatch):
    from app.repositories import fieldwork_repository as repo
    from app.services import fieldwork_service as svc

    captured: dict = {}

    async def fake_count_by_type(db, predicate=None):
        captured["by_type"] = predicate
        return {"repair": 2}

    async def fake_count_open_shortages(db, predicate=None):
        captured["open"] = predicate
        return 1

    monkeypatch.setattr(repo, "count_by_type", fake_count_by_type)
    monkeypatch.setattr(repo, "count_open_shortages", fake_count_open_shortages)

    user = SimpleNamespace(
        id=uuid4(),
        roles=[SimpleNamespace(data_scope=DataScope.SELF)],
        is_superuser=False,
        department_id=None,
    )
    summary = asyncio.run(svc.get_summary(None, user))

    assert summary.total == 2
    assert summary.open_shortages == 1
    assert captured["by_type"] is not None, "the type counts were unscoped"
    assert captured["open"] is not None, "the shortage count was unscoped"


def test_fieldwork_summary_is_unrestricted_for_an_all_scope_role(monkeypatch):
    from app.repositories import fieldwork_repository as repo
    from app.services import fieldwork_service as svc

    captured: dict = {}

    async def fake_count_by_type(db, predicate=None):
        captured["predicate"] = predicate
        return {}

    async def fake_count_open_shortages(db, predicate=None):
        return 0

    monkeypatch.setattr(repo, "count_by_type", fake_count_by_type)
    monkeypatch.setattr(repo, "count_open_shortages", fake_count_open_shortages)

    user = SimpleNamespace(
        id=uuid4(),
        roles=[SimpleNamespace(data_scope=DataScope.ALL)],
        is_superuser=False,
        department_id=None,
    )
    asyncio.run(svc.get_summary(None, user))

    # An ALL-scope role passes an unrestricted predicate, which compiles to true().
    from sqlalchemy.dialects import postgresql

    sql = str(captured["predicate"].compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "created_by" not in sql


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
