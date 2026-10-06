import os
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long!!")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:5432/erp_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


def _app_client():
    from app.core.deps import get_current_active_user
    from app.db.session import get_db
    from app.main import app

    async def _fake_user():
        return SimpleNamespace(id=uuid4(), is_superuser=True, is_active=True, roles=[])

    async def _fake_db():
        yield object()

    app.dependency_overrides[get_current_active_user] = _fake_user
    app.dependency_overrides[get_db] = _fake_db
    return app, TestClient(app)


def test_quote_approval_template_and_diff(monkeypatch):
    from app.domains.quote.application import quote_application_service

    async def _fake_create_template(db, payload, current_user):
        return {
            "id": str(uuid4()),
            "code": payload["template"]["code"],
            "name": payload["template"]["name"],
            "biz_type": "quote",
            "description": None,
            "is_active": True,
            "created_at": "2026-05-20T00:00:00Z",
            "updated_at": "2026-05-20T00:00:00Z",
            "created_by": str(current_user.id),
            "is_deleted": False,
        }

    async def _fake_detail(db, quote_id, current_user):
        # The diff route looks the quote up through the data-scope filtered detail service before comparing,
        # so that an out-of-scope quote answers 404 without threading a user through compare_quote_versions
        # (which the copilot also calls, as compare_fn).
        return {"id": str(quote_id)}

    async def _fake_diff(db, quote_id, from_version_no, to_version_no):
        return {
            "from_version": from_version_no,
            "to_version": to_version_no,
            "bom_diff": {"added": [], "removed": [], "changed": []},
            "cost_change": "100.00",
            "amount_change": "200.00",
            "profit_change": "100.00",
            "profit_rate_change": "0.0500",
        }

    monkeypatch.setattr(quote_application_service, "create_approval_template", _fake_create_template)
    monkeypatch.setattr(quote_application_service, "compare_quote_versions", _fake_diff)
    monkeypatch.setattr(quote_application_service, "get_quote_detail", _fake_detail)
    app, client = _app_client()
    try:
        r1 = client.post(
            "/api/v1/quotes/approval-templates",
            json={
                "template": {"code": "Q-L1", "name": "报价一级审批"},
                "nodes": [{"node_order": 1, "node_name": "销售经理", "min_amount": "0"}],
            },
        )
        assert r1.status_code == 201
        assert r1.json()["data"]["code"] == "Q-L1"

        r2 = client.get(f"/api/v1/quotes/{uuid4()}/versions/diff?from_version_no=1&to_version_no=2")
        assert r2.status_code == 200
        assert r2.json()["data"]["profit_change"] == "100.00"
    finally:
        app.dependency_overrides.clear()


def test_quote_export_async_endpoints(monkeypatch):
    from app.domains.quote.application import quote_application_service

    async def _fake_create_export_task(db, quote_id, export_format, current_user, template_id=None):
        return {
            "id": str(uuid4()),
            "quote_id": str(quote_id),
            "format": export_format,
            "status": "pending",
            "file_id": None,
            "error_message": None,
            "requested_at": "2026-05-20T00:00:00Z",
            "completed_at": None,
            "created_at": "2026-05-20T00:00:00Z",
            "updated_at": "2026-05-20T00:00:00Z",
            "created_by": str(current_user.id),
            "is_deleted": False,
        }

    async def _fake_process_pending(db, event_type):
        return {"requested": 1, "processed": 1, "failed": 0}

    monkeypatch.setattr(quote_application_service, "create_export_task", _fake_create_export_task)
    monkeypatch.setattr(quote_application_service, "process_pending_events", _fake_process_pending)
    app, client = _app_client()
    try:
        qid = uuid4()
        r1 = client.post(f"/api/v1/quotes/{qid}/exports", json={"format": "pdf"})
        assert r1.status_code == 202
        assert r1.json()["data"]["status"] == "pending"

        r2 = client.post("/api/v1/quotes/events/process-pending")
        assert r2.status_code == 200
        assert r2.json()["data"]["processed"] == 1
    finally:
        app.dependency_overrides.clear()
