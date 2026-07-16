import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.models.user import User
from veggie_app.services import auth_service, recipe_service


@pytest.fixture(autouse=True)
def _stub_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(recipe_service, "embed_text", lambda text: [0.0] * EMBEDDING_DIM)


def _login_as_admin(client: TestClient, db_session: Session) -> None:
    auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")
    db_session.flush()
    client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "correct horse battery"}
    )


def test_create_recipe_requires_admin_session(client: TestClient) -> None:
    response = client.post("/admin/recipes", json={"title": "Salade", "ingredients": ["laitue"]})

    assert response.status_code == 401


def test_create_recipe_rejects_non_admin(client: TestClient, db_session: Session) -> None:
    user = User(email="user@example.com", password_hash="irrelevant", is_admin=False)
    db_session.add(user)
    db_session.flush()
    raw_token = auth_service.create_session(db_session, user)
    client.cookies.set(auth_service.SESSION_COOKIE_NAME, raw_token)

    response = client.post("/admin/recipes", json={"title": "Salade", "ingredients": ["laitue"]})

    assert response.status_code == 403


def test_create_recipe_succeeds_for_admin(client: TestClient, db_session: Session) -> None:
    _login_as_admin(client, db_session)

    response = client.post(
        "/admin/recipes",
        json={
            "title": "Curry de lentilles corail",
            "ingredients": ["lentilles corail", "lait de coco", "curry"],
            "allergens": ["gluten"],
            "prep_time_minutes": 25,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Curry de lentilles corail"
    assert body["allergens"] == ["gluten"]
    assert body["prep_time_minutes"] == 25

    fetched = db_session.get(Recipe, body["id"])
    assert fetched is not None
    assert list(fetched.embedding) == [0.0] * EMBEDDING_DIM
