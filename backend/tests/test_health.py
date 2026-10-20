import pytest
from fastapi.testclient import TestClient

from veggie_app.config import settings
from veggie_app.main import api_docs_urls, app


def test_health_returns_ok() -> None:
    with TestClient(app) as test_client:
        response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_docs_are_served_in_development() -> None:
    assert api_docs_urls()["docs_url"] == "/docs"


def test_api_docs_are_disabled_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")

    assert api_docs_urls() == {"docs_url": None, "redoc_url": None, "openapi_url": None}
