"""Idempotency / duplicate guards for approval, settlement, receivable & payable.

Pins the existing service-layer refusals (duplicate submit, re-approve, over-settle) without
weakening confirm/void irreversible rules. Scenes C/D/E cover happy paths; these unit tests pin
the refusal branches so a regression cannot silently allow double-posting.
"""

from __future__ import annotations

import os
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("SECRET_KEY", "0123456789012345678901234567890123")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://erp:erp@127.0.0.1:55432/erp_db")


@pytest.mark.asyncio
async def test_quote_receivable_rejects_duplicate_active_request(monkeypatch):
    from app.services import quote_receivable_service as svc

    async def _enabled(db):
        return SimpleNamespace(quote_receivable_enabled=True)

    async def _load(*_a, **_k):
        raise HTTPException(status_code=400, detail="该报价已有进行中的应收申请")

    monkeypatch.setattr(svc, "_require_quote_receivable_enabled", _enabled)
    monkeypatch.setattr(svc, "_load_customer_quote", _load)

    with pytest.raises(HTTPException) as ei:
        await svc.create_request_from_quote(None, uuid4(), SimpleNamespace(id=uuid4()))
    assert ei.value.status_code == 400
    assert "进行中" in ei.value.detail


@pytest.mark.asyncio
async def test_quote_receivable_approve_only_when_pending(monkeypatch):
    from app.repositories import quote_receivable_repository as qrr_repo
    from app.services import quote_receivable_service as svc

    async def _enabled(db):
        return None

    async def _get(db, request_id):
        return SimpleNamespace(id=request_id, approval_status="approved", quote=None)

    monkeypatch.setattr(svc, "_require_quote_receivable_enabled", _enabled)
    monkeypatch.setattr(qrr_repo, "get_request", _get)

    with pytest.raises(HTTPException) as ei:
        await svc.approve_request(None, uuid4(), SimpleNamespace(id=uuid4()))
    assert ei.value.status_code == 400
    assert "仅待审批" in ei.value.detail


@pytest.mark.asyncio
async def test_quote_receivable_confirm_rejects_already_posted(monkeypatch):
    from app.repositories import quote_receivable_repository as qrr_repo
    from app.services import quote_receivable_service as svc

    async def _enabled(db):
        return None

    async def _get(db, request_id):
        return SimpleNamespace(
            id=request_id,
            approval_status="approved",
            receivable_entry_id=uuid4(),
            quote=None,
            quote_id=uuid4(),
        )

    monkeypatch.setattr(svc, "_require_quote_receivable_enabled", _enabled)
    monkeypatch.setattr(qrr_repo, "get_request", _get)

    with pytest.raises(HTTPException) as ei:
        await svc.confirm_receivable(None, uuid4(), SimpleNamespace(id=uuid4()))
    assert ei.value.status_code == 400
    assert "已确认" in ei.value.detail


@pytest.mark.asyncio
async def test_procurement_payable_rejects_duplicate_active(monkeypatch):
    from app.repositories import accounting_repository as accounting_repo
    from app.repositories import procurement_payable_repository as ppr_repo
    from app.repositories import procurement_repository as procurement_repo
    from app.services import procurement_payable_service as svc

    async def _enabled(db):
        return None

    entry = SimpleNamespace(
        id=uuid4(),
        payable_status="none",
        status="ordered",
        qty=Decimal("1"),
        unit_price=Decimal("100"),
        request_no="PR-1",
    )

    async def _get_entry(db, entry_id):
        return entry

    async def _existing(*_a, **_k):
        return None

    async def _active(*_a, **_k):
        return SimpleNamespace(id=uuid4())

    monkeypatch.setattr(svc, "_require_procurement_payable_enabled", _enabled)
    monkeypatch.setattr(procurement_repo, "get_entry", _get_entry)
    monkeypatch.setattr(accounting_repo, "get_entry_by_source", _existing)
    monkeypatch.setattr(ppr_repo, "get_active_request_by_entry", _active)

    with pytest.raises(HTTPException) as ei:
        await svc.create_request_from_entry(None, entry.id, SimpleNamespace(id=uuid4()))
    assert ei.value.status_code == 400
    assert "进行中" in ei.value.detail


@pytest.mark.asyncio
async def test_procurement_payable_approve_only_when_pending(monkeypatch):
    from app.repositories import procurement_payable_repository as ppr_repo
    from app.services import procurement_payable_service as svc

    async def _enabled(db):
        return None

    async def _get(db, request_id):
        return SimpleNamespace(id=request_id, approval_status="approved", payable_entry_id=None)

    monkeypatch.setattr(svc, "_require_procurement_payable_enabled", _enabled)
    monkeypatch.setattr(ppr_repo, "get_request", _get)

    with pytest.raises(HTTPException) as ei:
        await svc.approve_request(None, uuid4(), SimpleNamespace(id=uuid4()))
    assert ei.value.status_code == 400
    assert "仅待审批" in ei.value.detail


@pytest.mark.asyncio
async def test_receipt_over_settle_refused(monkeypatch):
    from datetime import date

    from app.repositories import accounting_repository as repo
    from app.schemas.accounting import ReceiptAllocationItem, ReceiptCreatePayload
    from app.services import ledger_service as svc

    async def _flags(db):
        return None

    rid = uuid4()
    customer_id = uuid4()

    async def _get_entry(db, entry_id, predicate=None, for_update=False):
        return SimpleNamespace(
            id=rid,
            entry_no="AR-1",
            entry_kind="receivable",
            status="confirmed",
            customer_id=customer_id,
            amount=Decimal("100.00"),
            settled_amount=Decimal("80.00"),
        )

    monkeypatch.setattr(svc, "require_accounting_enabled", _flags)
    monkeypatch.setattr(repo, "get_entry", _get_entry)
    monkeypatch.setattr(svc, "scope_predicate", lambda *a, **k: None)

    payload = ReceiptCreatePayload(
        customer_id=customer_id,
        amount=Decimal("50.00"),
        occurred_on=date.today(),
        title="over",
        allocations=[ReceiptAllocationItem(receivable_entry_id=rid, amount=Decimal("50.00"))],
    )
    with pytest.raises(HTTPException) as ei:
        await svc.create_receipt_with_allocations(None, payload, SimpleNamespace(id=uuid4(), is_superuser=True, roles=[]))
    assert ei.value.status_code == 400
    assert "不足" in ei.value.detail or "余额" in ei.value.detail


@pytest.mark.asyncio
async def test_payment_over_settle_refused(monkeypatch):
    from datetime import date

    from app.repositories import accounting_repository as repo
    from app.schemas.accounting import PaymentAllocationItem, PaymentCreatePayload
    from app.services import supplier_ledger_service as svc

    async def _req(db):
        return None

    async def _ensure(db, supplier_id):
        return None

    pid = uuid4()
    supplier_id = uuid4()

    async def _get_entry(db, entry_id, predicate=None, for_update=False):
        return SimpleNamespace(
            id=pid,
            entry_kind="payable",
            status="confirmed",
            supplier_id=supplier_id,
            amount=Decimal("100.00"),
            settled_amount=Decimal("90.00"),
        )

    monkeypatch.setattr(svc, "_require_accounting", _req)
    monkeypatch.setattr(svc, "_ensure_supplier_accessible", _ensure)
    monkeypatch.setattr(repo, "get_entry", _get_entry)
    monkeypatch.setattr(svc, "scope_predicate", lambda *a, **k: None)

    payload = PaymentCreatePayload(
        supplier_id=supplier_id,
        amount=Decimal("20.00"),
        occurred_on=date.today(),
        title="over",
        allocations=[PaymentAllocationItem(payable_entry_id=pid, amount=Decimal("20.00"))],
    )
    with pytest.raises(HTTPException) as ei:
        await svc.create_payment_with_allocations(None, payload, SimpleNamespace(id=uuid4(), is_superuser=True, roles=[]))
    assert ei.value.status_code == 400
    assert "Overpayment" in ei.value.detail


@pytest.mark.asyncio
async def test_confirm_entry_still_requires_draft(monkeypatch):
    """Irreversible confirm must not become a no-op shortcut on already-confirmed rows."""
    from app.repositories import accounting_repository as repo
    from app.services import accounting_service as svc

    async def _flags(db):
        return None

    async def _get(db, entry_id, predicate=None, for_update=False):
        return SimpleNamespace(id=entry_id, status="confirmed", entry_no="AR-9")

    monkeypatch.setattr(svc, "require_accounting_enabled", _flags)
    monkeypatch.setattr(repo, "get_entry", _get)
    monkeypatch.setattr(svc, "scope_predicate", lambda *a, **k: None)

    with pytest.raises(HTTPException) as ei:
        await svc.confirm_entry(None, uuid4(), SimpleNamespace(id=uuid4(), is_superuser=True, roles=[]))
    assert ei.value.status_code == 400
    assert "草稿" in ei.value.detail


@pytest.mark.asyncio
async def test_void_entry_still_rejects_double_void(monkeypatch):
    from app.repositories import accounting_repository as repo
    from app.services import accounting_service as svc

    async def _flags(db):
        return None

    async def _get(db, entry_id, predicate=None, for_update=False):
        return SimpleNamespace(id=entry_id, status="void", entry_kind="receivable", settled_amount=0)

    monkeypatch.setattr(svc, "require_accounting_enabled", _flags)
    monkeypatch.setattr(repo, "get_entry", _get)
    monkeypatch.setattr(svc, "scope_predicate", lambda *a, **k: None)

    with pytest.raises(HTTPException) as ei:
        await svc.void_entry(None, uuid4(), SimpleNamespace(id=uuid4(), is_superuser=True, roles=[]))
    assert ei.value.status_code == 400
    assert "已作废" in ei.value.detail


def test_load_customer_quote_duplicate_guards_are_source_pinned():
    """Static pin: the three duplicate guards stay in the load path (not only in tests)."""
    import inspect

    from app.services import quote_receivable_service as svc

    src = inspect.getsource(svc._load_customer_quote)
    assert "已生成应收" in src
    assert "有效应收" in src
    assert "进行中的应收申请" in src
