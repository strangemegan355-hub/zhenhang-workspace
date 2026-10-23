"""Tests for B1 accounting enhancements: due_date, date filter, export, supplier ledger."""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long!!")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://erp:erp@127.0.0.1:5432/erp_db")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")

from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient


def _make_client():
    from app.core.deps import get_current_active_user
    from app.db.session import get_db
    from app.main import app

    async def _fake_user():
        return SimpleNamespace(id=uuid4(), is_superuser=True, is_active=True, roles=[])

    async def _fake_db():
        yield object()

    app.dependency_overrides = {get_current_active_user: _fake_user, get_db: _fake_db}
    return app, TestClient(app)


def test_due_date_in_create(monkeypatch):
    """due_date is accepted in create payload."""
    from app.services import accounting_service as svc
    from uuid import UUID

    async def _fake_create(db, payload, current_user, *, allow_backfill):
        assert getattr(payload, "due_date", None) is not None, "due_date should be set"
        return SimpleNamespace(id=UUID("0" * 32), entry_no="AR-001",
            entry_kind="receivable", status="draft", customer_id=uuid4(),
            supplier_id=None, project_id=None, quote_id=None, amount=50000.0,
            settled_amount=0, currency="CNY", occurred_on="2026-06-28",
            due_date="2026-07-28", booked_on="2026-06-28", is_backfill=False,
            source_type="manual", source_id=None, source_no=None,
            approval_status="none", title="test", remark=None, lines=[],
            created_at="2026-06-28", updated_at="2026-06-28", created_by=uuid4())

    async def _fake_enabled(db):
        return None

    monkeypatch.setattr(svc, "create_entry", _fake_create)
    monkeypatch.setattr(svc, "require_accounting_enabled", _fake_enabled)

    app, client = _make_client()
    try:
        resp = client.post("/api/v1/accounting/entries", json={
            "entry_kind": "receivable", "customer_id": str(uuid4()),
            "amount": 50000, "occurred_on": "2026-06-28",
            "due_date": "2026-07-28", "title": "test",
        })
        assert resp.status_code == 201, resp.text
    finally:
        app.dependency_overrides.clear()


def test_date_filter_in_list(monkeypatch):
    """date_from/date_to reach service layer."""
    from app.services import accounting_service as svc

    called = {}

    class FakePage:
        total = 0
        page = 1
        page_size = 20
        items = []

    async def _fake_list(db, **kw):
        called.update(kw)
        return FakePage()

    async def _fake_enabled(db):
        return None

    monkeypatch.setattr(svc, "list_entries", _fake_list)
    monkeypatch.setattr(svc, "require_accounting_enabled", _fake_enabled)

    app, client = _make_client()
    try:
        resp = client.get("/api/v1/accounting/entries", params={
            "date_from": "2026-01-01", "date_to": "2026-06-30",
        })
        assert resp.status_code == 200, resp.text
        assert called.get("date_from") is not None
        assert called.get("date_to") is not None
    finally:
        app.dependency_overrides.clear()


def test_export_csv(monkeypatch):
    """GET /entries/export returns CSV."""
    from app.services import accounting_service as svc
    from app.schemas.accounting import AccountingEntryRead
    from datetime import date
    from decimal import Decimal
    from uuid import UUID

    fake = AccountingEntryRead(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        entry_no="AR-20260628-001", entry_kind="receivable", status="draft",
        customer_id=UUID("00000000-0000-0000-0000-000000000002"),
        supplier_id=None, project_id=None, quote_id=None,
        amount=Decimal("50000.00"), settled_amount=Decimal("0"),
        currency="CNY", occurred_on=date.today(), due_date=None,
        booked_on=date.today(), is_backfill=False,
        source_type="manual", approval_status="none",
        title="测试应收", remark=None,
        created_at=date.today(), updated_at=date.today(),
        created_by=UUID("00000000-0000-0000-0000-000000000003"),
        lines=[],
    )

    class FakeResult:
        items = [fake]

    async def _fake_list(db, **kw):
        return FakeResult()

    async def _fake_enabled(db):
        return None

    monkeypatch.setattr(svc, "list_entries", _fake_list)
    monkeypatch.setattr(svc, "require_accounting_enabled", _fake_enabled)

    app, client = _make_client()
    try:
        resp = client.get("/api/v1/accounting/entries/export")
        assert resp.status_code == 200, resp.text
        assert "text/csv" in resp.headers.get("content-type", "")
        assert "单号" in resp.text
        assert "AR-20260628-001" in resp.text
    finally:
        app.dependency_overrides.clear()


def test_supplier_ledger_list(monkeypatch):
    """GET /ledger/suppliers returns paginated."""
    from app.services import supplier_ledger_service as sls

    async def _fake(db, **kw):
        from app.schemas.common import PageResponse
        return PageResponse(total=5, page=1, page_size=20, items=[])

    monkeypatch.setattr(sls, "get_supplier_ledger_summaries", _fake)
    monkeypatch.setattr(sls, "_require_accounting", lambda db: None)

    app, client = _make_client()
    try:
        resp = client.get("/api/v1/accounting/ledger/suppliers")
        assert resp.status_code == 200, resp.text
    finally:
        app.dependency_overrides.clear()


def test_supplier_ledger_detail(monkeypatch):
    """GET /ledger/suppliers/{id} returns detail."""
    from app.services import supplier_ledger_service as sls
    from app.schemas.accounting import SupplierLedgerDetailRead
    from decimal import Decimal
    from uuid import UUID

    sid = UUID("00000000-0000-0000-0000-000000000010")
    fake = SupplierLedgerDetailRead(
        supplier_id=sid, supplier_name="测试供应商", supplier_code="S001",
        is_registered=True, payable_total=Decimal("100000"),
        paid_total=Decimal("30000"), outstanding_total=Decimal("70000"),
        entries=[],
    )

    async def _fake(db, supplier_id, current_user=None):
        return fake

    monkeypatch.setattr(sls, "get_supplier_ledger_detail", _fake)
    monkeypatch.setattr(sls, "_require_accounting", lambda db: None)

    app, client = _make_client()
    try:
        resp = client.get(f"/api/v1/accounting/ledger/suppliers/{sid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        inner = data.get("data", data)
        assert "supplier_name" in inner or "supplier_name" in data
    finally:
        app.dependency_overrides.clear()


def test_supplier_ledger_register(monkeypatch):
    """POST /ledger/suppliers registers a supplier."""
    from app.services import supplier_ledger_service as sls
    from app.schemas.accounting import SupplierLedgerDetailRead
    from decimal import Decimal

    sid = str(uuid4())

    async def _fake_register(db, payload, uid, current_user=None):
        return SimpleNamespace(supplier_id=sid, created_by=uid)

    async def _fake_detail(db, _sid, current_user=None):
        return SupplierLedgerDetailRead(
            supplier_id=_sid, supplier_name="新供应商", supplier_code=None,
            is_registered=True, payable_total=Decimal("0"),
            paid_total=Decimal("0"), outstanding_total=Decimal("0"),
            entries=[],
        )

    monkeypatch.setattr(sls, "register_supplier", _fake_register)
    monkeypatch.setattr(sls, "get_supplier_ledger_detail", _fake_detail)
    monkeypatch.setattr(sls, "_require_accounting", lambda db: None)

    app, client = _make_client()
    try:
        resp = client.post("/api/v1/accounting/ledger/suppliers", json={"supplier_id": sid})
        assert resp.status_code in (200, 201), resp.text
    finally:
        app.dependency_overrides.clear()


def test_supplier_payment(monkeypatch):
    """POST /ledger/payments creates payment."""
    from app.services import supplier_ledger_service as sls

    async def _fake(db, payload, uid, current_user=None):
        from app.schemas.accounting import LedgerEntryRead
        from decimal import Decimal
        return LedgerEntryRead(
            id=uuid4(), entry_no="PY-001", entry_kind="payment", status="confirmed",
            customer_id=None, amount=Decimal("5000"), settled_amount=Decimal("0"),
            open_amount=Decimal("5000"), payment_status="unpaid",
            source_type="manual", source_label="手录", source_no=None,
            quote_id=None, occurred_on="2026-06-28", title="付款测试",
            remark=None, is_backfill=False, allocations=[],
        )

    monkeypatch.setattr(sls, "create_payment_with_allocations", _fake)
    monkeypatch.setattr(sls, "_require_accounting", lambda db: None)

    app, client = _make_client()
    try:
        resp = client.post("/api/v1/accounting/ledger/payments", json={
            "supplier_id": str(uuid4()), "amount": 5000,
            "occurred_on": "2026-06-28", "title": "付款测试",
            "allocations": [{"payable_entry_id": str(uuid4()), "amount": 5000}],
        })
        assert resp.status_code == 201, resp.text
    finally:
        app.dependency_overrides.clear()


def test_all_new_modules_import():
    """Verify all B1 modules import without error."""
    from app.models.supplier_ledger_account import SupplierLedgerAccount
    from app.services.supplier_ledger_service import (
        register_supplier, get_supplier_ledger_summaries,
        get_supplier_ledger_detail, create_manual_payable,
        create_payment_with_allocations,
    )
    from app.schemas.accounting import (
        SupplierLedgerSummaryRead, SupplierLedgerDetailRead, PaymentCreatePayload,
    )
    from app.repositories.accounting_repository import (
        list_entries, get_supplier_ledger_account,
        register_supplier_ledger_account, supplier_ledger_rows,
    )
    from app.models.accounting_entry import AccountingEntry
    import inspect

    cols = [c.name for c in AccountingEntry.__table__.columns]
    assert "due_date" in cols
    assert "supplier_id" in cols
    sig = inspect.signature(list_entries)
    assert "date_from" in sig.parameters
    assert "date_to" in sig.parameters
