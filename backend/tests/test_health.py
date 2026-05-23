from fastapi.testclient import TestClient


def test_health_live() -> None:
    # Import after conftest sets env vars (pytest loads conftest first).
    from app.main import app

    client = TestClient(app)
    resp = client.get("/api/v1/health/live")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "SUCCESS"
    assert body["data"]["status"] == "ok"
