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
        return SimpleNamespace(id=uuid4(), is_superuser=True, is_active=True)

    async def _fake_db():
        yield object()

    app.dependency_overrides[get_current_active_user] = _fake_user
    app.dependency_overrides[get_db] = _fake_db
    return app, TestClient(app)


def test_machine_create_openapi_example_and_response(monkeypatch) -> None:
    from app.services import machine_service

    async def _fake_create_machine(db, payload, current_user):
        return {
            "id": str(uuid4()),
            "category_id": None,
            "code": payload["code"],
            "machine_code": "INJ2-20260520-0001",
            "name": payload["name"],
            "model_no": payload.get("model_no"),
            "status": "draft",
            "description": payload.get("description"),
            "created_at": "2026-05-20T00:00:00Z",
            "updated_at": "2026-05-20T00:00:00Z",
            "created_by": str(current_user.id),
            "is_deleted": False,
        }

    monkeypatch.setattr(machine_service, "create_machine", _fake_create_machine)
    app, client = _app_client()
    try:
        resp = client.post(
            "/api/v1/machines",
            json={"category_id": None, "code": "INJ-280T", "name": "280T 注塑机", "status": "draft"},
        )
        assert resp.status_code == 201
        assert resp.json()["code"] == "SUCCESS"
        assert resp.json()["data"]["machine_code"].startswith("INJ2-")
    finally:
        app.dependency_overrides.clear()


def test_bom_batch_and_transition_api(monkeypatch) -> None:
    from app.services import machine_service

    async def _fake_batch(db, items, current_user):
        return [
            {
                "id": str(uuid4()),
                **item,
                "line_total": "4200.5000",
                "created_at": "2026-05-20T00:00:00Z",
                "updated_at": "2026-05-20T00:00:00Z",
                "created_by": str(current_user.id),
                "is_deleted": False,
            }
            for item in items
        ]

    async def _fake_transition(db, bom_id, action_code, current_user):
        return {
            "id": str(bom_id),
            "machine_id": str(uuid4()),
            "version": "V1.0",
            "is_active": True,
            "effective_date": "2026-06-01",
            "total_cost": "8000.0000",
            "status": "approved",
            "remark": None,
            "created_at": "2026-05-20T00:00:00Z",
            "updated_at": "2026-05-20T00:00:00Z",
            "created_by": str(current_user.id),
            "is_deleted": False,
        }

    monkeypatch.setattr(machine_service, "create_bom_items_batch", _fake_batch)
    monkeypatch.setattr(machine_service, "transition_bom_status", _fake_transition)
    app, client = _app_client()
    bom_id = uuid4()
    try:
        batch_resp = client.post(
            "/api/v1/boms/items/batch",
            json={
                "items": [
                    {
                        "bom_id": str(bom_id),
                        "item_code": "SCREW-M30",
                        "item_name": "螺杆总成",
                        "spec": "M30",
                        "unit": "set",
                        "quantity": "1.0000",
                        "unit_cost": "4200.5000",
                        "line_total": "0",
                        "loss_rate": "0.0100",
                        "sort_order": 1,
                    }
                ]
            },
        )
        assert batch_resp.status_code == 201
        assert batch_resp.json()["code"] == "SUCCESS"
        assert len(batch_resp.json()["data"]) == 1

        trans_resp = client.post(
            f"/api/v1/boms/{bom_id}/actions/transition",
            json={"action_code": "submit"},
        )
        assert trans_resp.status_code == 200
        assert trans_resp.json()["data"]["status"] == "approved"
    finally:
        app.dependency_overrides.clear()


def test_unique_violation_returns_standard_error(monkeypatch) -> None:
    from app.core.exceptions import UniqueViolationException
    from app.services import machine_service

    async def _raise_unique(*args, **kwargs):
        raise UniqueViolationException("machine.machine_code", "INJ2-20260520-0001")

    monkeypatch.setattr(machine_service, "create_machine", _raise_unique)
    app, client = _app_client()
    try:
        resp = client.post(
            "/api/v1/machines",
            json={"category_id": None, "code": "INJ-280T", "name": "280T 注塑机", "status": "draft"},
        )
        assert resp.status_code == 409
        body = resp.json()
        assert body["code"] == "UNIQUE_VIOLATION"
        assert "already exists" in body["message"]
    finally:
        app.dependency_overrides.clear()
