import os
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long!!")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:5432/erp_db")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")


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


def test_quote_create_endpoint(monkeypatch):
    from app.domains.quote.application import quote_application_service

    async def _fake_create(db, payload, current_user):
        return {
            "id": str(uuid4()),
            "quote_no": "Q20260520-0001",
            "title": payload["title"],
            "customer_id": str(payload["customer_id"]),
            "machine_id": str(payload["machine_id"]),
            "bom_id": None,
                "approval_template_id": payload.get("approval_template_id"),
                "current_approval_order": 0,
            "workflow_state": "draft",
            "currency": "CNY",
            "total_amount": "0",
            "valid_until": None,
            "remark": None,
            "created_at": "2026-05-20T00:00:00Z",
            "updated_at": "2026-05-20T00:00:00Z",
            "created_by": str(current_user.id),
            "is_deleted": False,
        }

    monkeypatch.setattr(quote_application_service, "create_quote", _fake_create)
    app, client = _app_client()
    try:
        resp = client.post(
            "/api/v1/quotes",
            json={
                "title": "注塑机报价单",
                "customer_id": str(uuid4()),
                "machine_id": str(uuid4()),
                "bom_id": None,
                "currency": "CNY",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["code"] == "SUCCESS"
        assert body["data"]["quote_no"].startswith("Q")
    finally:
        app.dependency_overrides.clear()
