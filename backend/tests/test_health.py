from fastapi.testclient import TestClient

from veggie_app.main import app


def test_health_returns_ok() -> None:
    with TestClient(app) as test_client:
        response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
