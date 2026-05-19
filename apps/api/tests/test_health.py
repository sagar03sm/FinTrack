from fastapi.testclient import TestClient


def test_health_endpoint():
    # Import inside the test so settings/logging are initialized fresh.
    from app.main import app

    with TestClient(app) as client:
        # /health should not require DB connectivity
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
