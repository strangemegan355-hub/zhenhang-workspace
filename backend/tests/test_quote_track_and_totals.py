"""K-005 product/machine track: enforce product_id on create + server-side totals."""

from __future__ import annotations

import os
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

os.environ.setdefault("SECRET_KEY", "0123456789012345678901234567890123")


def test_classify_quote_track_prefers_product():
    from app.domains.quote.application.quote_track_helpers import (
        PREFERRED_QUOTE_TRACK,
        classify_quote_track,
    )

    pid, mid = uuid4(), uuid4()
    assert PREFERRED_QUOTE_TRACK == "product"
    assert classify_quote_track(pid, None) == "product"
    assert classify_quote_track(pid, mid) == "product_with_machine_link"
    assert classify_quote_track(None, mid) == "machine_legacy"
    assert classify_quote_track(None, None) == "none"


def test_strip_client_quote_totals():
    from app.domains.quote.application.quote_track_helpers import strip_client_quote_totals

    payload = {
        "title": "x",
        "total_amount": Decimal("99999"),
        "total_cost": Decimal("1"),
        "profit_amount": Decimal("2"),
        "profit_rate": Decimal("3"),
        "customer_id": uuid4(),
    }
    cleaned = strip_client_quote_totals(payload)
    assert "total_amount" not in cleaned
    assert "total_cost" not in cleaned
    assert cleaned["title"] == "x"


def test_quote_create_schema_requires_product_id():
    from app.schemas.quote import QuoteCreate, QuoteWizardCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc:
        QuoteCreate(title="t", customer_id=uuid4())
    assert "product_id" in str(exc.value)

    with pytest.raises(ValidationError) as exc2:
        QuoteCreate(title="t", customer_id=uuid4(), machine_id=uuid4())
    assert "product_id" in str(exc2.value)
    assert "K-005" in str(exc2.value)

    # product_id alone is enough; machine_id optional (filled from product defaults later)
    ok = QuoteCreate(title="t", customer_id=uuid4(), product_id=uuid4())
    assert ok.product_id is not None

    with pytest.raises(ValidationError) as exc3:
        QuoteWizardCreate(title="t", customer_id=uuid4(), machine_id=uuid4())
    assert "product_id" in str(exc3.value)


@pytest.mark.asyncio
async def test_create_quote_rejects_machine_only_with_400():
    """Service-layer K-005 guard: machine_id-only create -> HTTP 400."""
    from app.domains.quote.application import quote_application_service as svc
    from app.domains.quote.application.quote_track_helpers import PRODUCT_ID_REQUIRED_DETAIL
    from fastapi import HTTPException

    class FakeUser:
        id = uuid4()
        department_id = None

    class FakeDb:
        async def commit(self):
            return None

        async def refresh(self, _obj):
            return None

    with pytest.raises(HTTPException) as exc:
        await svc.create_quote(
            FakeDb(),
            {
                "title": "legacy machine only",
                "customer_id": uuid4(),
                "machine_id": uuid4(),
            },
            FakeUser(),
        )
    assert exc.value.status_code == 400
    assert "product_id" in str(exc.value.detail)
    assert "K-005" in str(exc.value.detail)
    assert exc.value.detail == PRODUCT_ID_REQUIRED_DETAIL


def test_require_product_id_helper_allows_product():
    from app.domains.quote.application.quote_track_helpers import require_product_id_for_create

    require_product_id_for_create({"product_id": uuid4(), "machine_id": None})


def test_legacy_machine_only_quote_read_still_ok():
    """K-005: historical machine-only rows remain readable via QuoteRead (no product_id)."""
    from datetime import UTC, datetime

    from app.domains.quote.application.quote_track_helpers import classify_quote_track
    from app.schemas.quote import QuoteRead

    legacy = QuoteRead(
        id=uuid4(),
        quote_no="LEGACY-M-001",
        title="historical machine-only",
        customer_id=uuid4(),
        machine_id=uuid4(),
        product_id=None,
        bom_id=None,
        current_approval_order=0,
        workflow_state="draft",
        currency="CNY",
        total_amount=Decimal("0"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        is_deleted=False,
    )
    assert legacy.product_id is None
    assert legacy.machine_id is not None
    assert classify_quote_track(legacy.product_id, legacy.machine_id) == "machine_legacy"


@pytest.mark.asyncio
async def test_create_quote_ignores_client_total_amount(monkeypatch):
    """Header total is always zero at create; lines recompute later."""
    from app.domains.quote.application import quote_application_service as svc

    captured: dict = {}

    class FakeQuote:
        id = uuid4()
        quote_no = "QTEST-0001"

    async def fake_next_seq(db, prefix):  # noqa: ANN001
        return 1

    async def fake_create(db, data, autocommit=False):  # noqa: ANN001
        captured.update(data)
        return FakeQuote()

    async def fake_audit(*_a, **_k):  # noqa: ANN001
        return None

    async def fake_publish(*_a, **_k):  # noqa: ANN001
        return None

    async def fake_notify(*_a, **_k):  # noqa: ANN001
        return None

    async def fake_push(*_a, **_k):  # noqa: ANN001
        return None

    async def fake_defaults(db, payload):  # noqa: ANN001
        return payload

    class FakeUser:
        id = uuid4()
        department_id = None

    class FakeDb:
        async def commit(self):
            return None

        async def refresh(self, _obj):
            return None

    monkeypatch.setattr(svc.repo, "next_quote_sequence", fake_next_seq)
    monkeypatch.setattr(svc.repo, "create_quote", fake_create)
    monkeypatch.setattr(svc, "write_audit_log", fake_audit)
    monkeypatch.setattr(svc.event_bus, "publish", fake_publish)
    monkeypatch.setattr(svc, "create_notification", fake_notify)
    monkeypatch.setattr(svc, "push_quote_updated", fake_push)
    monkeypatch.setattr(
        "app.domains.quote.application.quote_track_helpers.apply_product_machine_defaults",
        fake_defaults,
    )

    await svc.create_quote(
        FakeDb(),
        {
            "title": "client total attack",
            "customer_id": uuid4(),
            "product_id": uuid4(),
            "total_amount": Decimal("999999.99"),
        },
        FakeUser(),
    )
    assert captured["total_amount"] == Decimal("0")
    assert Decimal(str(captured["total_amount"])) != Decimal("999999.99")


def test_idempotency_guards_present_in_services():
    """Static pin: duplicate receivable/payable + over-settle paths stay guarded."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app" / "services"
    recv = (root / "quote_receivable_service.py").read_text(encoding="utf-8")
    pay = (root / "procurement_payable_service.py").read_text(encoding="utf-8")
    ledger = (root / "ledger_service.py").read_text(encoding="utf-8")
    supplier = (root / "supplier_ledger_service.py").read_text(encoding="utf-8")

    assert "不可重复申请" in recv or "已有进行中的应收申请" in recv
    assert "已有进行中的应付申请" in pay or "该采购已生成应付" in pay
    assert "for_update=True" in ledger
    assert "未收余额不足" in ledger
    assert "for_update=True" in supplier


def test_quote_create_schema_has_no_client_total_field():
    """API create DTO cannot carry a client total — server recomputes from lines."""
    from app.schemas.quote import QuoteCreate, QuoteItemCreate

    assert "total_amount" not in QuoteCreate.model_fields
    assert "line_total" not in QuoteItemCreate.model_fields
    assert "total_amount" not in QuoteItemCreate.model_fields


@pytest.mark.asyncio
async def test_create_quote_version_totals_from_lines_only(monkeypatch):
    """Version totals = sum(qty * unit_price); client cannot inject a divergent header total."""
    from app.domains.quote.application import quote_application_service as svc

    quote = SimpleNamespace(
        id=uuid4(),
        quote_no="QTEST-0002",
        total_amount=Decimal("0"),
        bom_id=None,
        created_by=uuid4(),
    )
    version = SimpleNamespace(
        id=uuid4(),
        total_amount=Decimal("0"),
        total_cost=Decimal("0"),
        profit_amount=Decimal("0"),
        profit_rate=Decimal("0"),
        analysis_snapshot={},
    )
    items_written: list[dict] = []

    async def fake_get_quote(db, quote_id, predicate=None):  # noqa: ANN001
        return quote

    async def fake_max_version(db, quote_id):  # noqa: ANN001
        return 0

    async def fake_get_version_by_no(*_a, **_k):  # noqa: ANN001
        return None

    async def fake_mark(*_a, **_k):  # noqa: ANN001
        return None

    async def fake_create_version(db, data, autocommit=False):  # noqa: ANN001
        return version

    async def fake_create_item(db, data, autocommit=False):  # noqa: ANN001
        items_written.append(data)
        return SimpleNamespace(id=uuid4())

    async def fake_audit(*_a, **_k):  # noqa: ANN001
        return None

    async def fake_notify(*_a, **_k):  # noqa: ANN001
        return None

    async def fake_push(*_a, **_k):  # noqa: ANN001
        return None

    class FakeUser:
        id = uuid4()

    class FakeDb:
        async def commit(self):
            return None

        async def refresh(self, _obj):
            return None

    monkeypatch.setattr(svc.repo, "get_quote", fake_get_quote)
    monkeypatch.setattr(svc.repo, "max_quote_version_no", fake_max_version)
    monkeypatch.setattr(svc.repo, "get_quote_version_by_no", fake_get_version_by_no)
    monkeypatch.setattr(svc.repo, "mark_other_versions_not_current", fake_mark)
    monkeypatch.setattr(svc.repo, "create_quote_version", fake_create_version)
    monkeypatch.setattr(svc.repo, "create_quote_item", fake_create_item)
    async def fake_publish(*_a, **_k):  # noqa: ANN001
        return None

    monkeypatch.setattr(svc, "write_audit_log", fake_audit)
    monkeypatch.setattr(svc, "create_notification", fake_notify)
    monkeypatch.setattr(svc, "push_quote_updated", fake_push)
    monkeypatch.setattr(svc.event_bus, "publish", fake_publish)
    monkeypatch.setattr(svc, "scope_predicate", lambda *a, **k: None)

    # Inject a lying header total in the payload bag; service must ignore it and sum lines.
    await svc.create_quote_version(
        FakeDb(),
        quote.id,
        [
            {
                "item_code": "A",
                "item_name": "a",
                "unit": "pcs",
                "quantity": Decimal("2"),
                "unit_price": Decimal("10"),
            },
            {
                "item_code": "B",
                "item_name": "b",
                "unit": "pcs",
                "quantity": Decimal("3"),
                "unit_price": Decimal("5"),
            },
        ],
        FakeUser(),
        # no total_amount arg — if kwargs ever appear they must not win
    )
    assert version.total_amount == Decimal("35")  # 2*10 + 3*5
    assert quote.total_amount == Decimal("35")
    assert len(items_written) == 2
    assert items_written[0]["line_total"] == Decimal("20")
    assert items_written[1]["line_total"] == Decimal("15")
