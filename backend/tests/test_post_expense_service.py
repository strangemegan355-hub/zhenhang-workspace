"""The single post-expense implementation, pinned by tests.

Before this round the same logic lived inline in two endpoints and nothing tested it. Now that it is
one function, its behaviour is worth holding still — this is the accounting path, and the two copies
had already diverged in six fields.

`accounting_service.repo` and `AccountingEntryRead` are replaced with fakes so the assertions can be
about the payload the service builds, which is exactly what the endpoints used to build by hand.
"""

from __future__ import annotations

import os
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-32")

import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402

from app.schemas.accounting import PostExpensePayload  # noqa: E402
from app.services import accounting_service as svc  # noqa: E402


class _ReadStub:
    """Stands in for AccountingEntryRead: the test asserts on the payload, not the serialisation."""

    @staticmethod
    def model_validate(value):  # noqa: ANN001, ANN205
        return value


@pytest.fixture
def captured(monkeypatch):
    """Capture the entry payload the service hands to the repository."""
    seen: dict = {}

    async def fake_generate_entry_no(db, kind):  # noqa: ANN001, ANN202
        seen["entry_no_kind"] = kind
        return "EXP-0001"

    async def fake_create_entry(db, payload):  # noqa: ANN001, ANN202
        seen.update(payload)
        return SimpleNamespace(id=uuid4())

    async def fake_get_entry(db, entry_id):  # noqa: ANN001, ANN202
        return None

    async def fake_require_enabled(db):  # noqa: ANN001, ANN202
        return None

    monkeypatch.setattr(svc.repo, "generate_entry_no", fake_generate_entry_no)
    monkeypatch.setattr(svc.repo, "create_entry", fake_create_entry)
    monkeypatch.setattr(svc.repo, "get_entry", fake_get_entry)
    monkeypatch.setattr(svc, "require_accounting_enabled", fake_require_enabled)
    monkeypatch.setattr(svc, "AccountingEntryRead", _ReadStub)
    return seen


async def test_a_work_order_expense_is_posted_as_confirmed_and_linked(captured):
    work_order_id, customer_id, project_id, user_id = uuid4(), uuid4(), uuid4(), uuid4()
    work_order = SimpleNamespace(
        work_order_no="WO-2026-001", customer_id=customer_id, project_id=project_id
    )

    async def fake_get_work_order(db, identifier):  # noqa: ANN001, ANN202
        assert identifier == work_order_id
        return work_order

    from app.repositories import work_order_repository

    original = work_order_repository.get_work_order
    work_order_repository.get_work_order = fake_get_work_order
    try:
        await svc.post_work_order_expense(
            None,
            work_order_id,
            PostExpensePayload(amount=Decimal("12.50"), title="  coating  ", remark="  note  "),
            SimpleNamespace(id=user_id),
        )
    finally:
        work_order_repository.get_work_order = original

    assert captured["status"] == "confirmed"
    assert captured["entry_kind"] == "expense"
    assert captured["entry_no_kind"] == "expense"
    assert captured["source_type"] == "work_order"
    assert captured["source_id"] == work_order_id
    assert captured["source_no"] == "WO-2026-001"
    assert captured["customer_id"] == customer_id
    assert captured["project_id"] == project_id
    assert captured["created_by"] == user_id
    # The inline copies passed float(payload.amount) to a numeric column.
    assert captured["amount"] == Decimal("12.50")
    assert isinstance(captured["amount"], Decimal)
    assert captured["settled_amount"] == Decimal("0")
    assert captured["currency"] == "CNY"
    assert captured["is_backfill"] is False
    assert captured["approval_status"] == "none"
    assert captured["party_type"] is None and captured["supplier_id"] is None
    assert captured["title"] == "coating"
    assert captured["remark"] == "note"


async def test_a_cost_estimate_expense_carries_no_customer_or_project(captured):
    estimate_id, user_id = uuid4(), uuid4()
    estimate = SimpleNamespace(estimate_no="CE-2026-009")

    from app.repositories import cost_estimate_repository

    original = cost_estimate_repository.get_cost_estimate
    cost_estimate_repository.get_cost_estimate = lambda db, identifier: _return(estimate)
    try:
        await svc.post_cost_estimate_expense(
            None,
            estimate_id,
            PostExpensePayload(amount=Decimal("3"), title="estimate", remark=None),
            SimpleNamespace(id=user_id),
        )
    finally:
        cost_estimate_repository.get_cost_estimate = original

    assert captured["source_type"] == "cost_estimate"
    assert captured["source_id"] == estimate_id
    assert captured["source_no"] == "CE-2026-009"
    assert captured["customer_id"] is None
    assert captured["project_id"] is None
    assert captured["remark"] is None
    assert captured["created_by"] == user_id


async def _return(value):  # noqa: ANN202
    return value


async def test_a_missing_work_order_is_a_404(captured):
    from app.repositories import work_order_repository

    original = work_order_repository.get_work_order
    work_order_repository.get_work_order = lambda db, identifier: _return(None)
    try:
        with pytest.raises(HTTPException) as error:
            await svc.post_work_order_expense(
                None,
                uuid4(),
                PostExpensePayload(amount=Decimal("1"), title="missing"),
                SimpleNamespace(id=uuid4()),
            )
    finally:
        work_order_repository.get_work_order = original

    assert error.value.status_code == 404
    assert error.value.detail == "Work order not found"


async def test_a_missing_estimate_is_a_404(captured):
    from app.repositories import cost_estimate_repository

    original = cost_estimate_repository.get_cost_estimate
    cost_estimate_repository.get_cost_estimate = lambda db, identifier: _return(None)
    try:
        with pytest.raises(HTTPException) as error:
            await svc.post_cost_estimate_expense(
                None,
                uuid4(),
                PostExpensePayload(amount=Decimal("1"), title="missing"),
                SimpleNamespace(id=uuid4()),
            )
    finally:
        cost_estimate_repository.get_cost_estimate = original

    assert error.value.status_code == 404
    assert error.value.detail == "Cost estimate not found"
