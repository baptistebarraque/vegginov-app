import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.models.user import User
from veggie_app.services import auth_service, recipe_service

VALID_CSV = "title,ingredients,allergens\nCurry,lentilles; curry,gluten\nSalade,laitue,\n"


@pytest.fixture(autouse=True)
def _stub_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(recipe_service, "embed_text", lambda text: [0.0] * EMBEDDING_DIM)


def _login_as_admin(client: TestClient, db_session: Session) -> None:
    auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")
    db_session.flush()
    client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "correct horse battery"}
    )


def _upload_csv(client: TestClient, content: str):
    return client.post(
        "/admin/recipes/import",
        files={"file": ("recipes.csv", content.encode("utf-8"), "text/csv")},
    )


def test_import_requires_admin_session(client: TestClient) -> None:
    response = _upload_csv(client, VALID_CSV)

    assert response.status_code == 401


def test_import_rejects_non_admin(client: TestClient, db_session: Session) -> None:
    user = User(email="user@example.com", password_hash="irrelevant", is_admin=False)
    db_session.add(user)
    db_session.flush()
    raw_token = auth_service.create_session(db_session, user)
    client.cookies.set(auth_service.SESSION_COOKIE_NAME, raw_token)

    response = _upload_csv(client, VALID_CSV)

    assert response.status_code == 403


def test_import_succeeds_for_admin(client: TestClient, db_session: Session) -> None:
    _login_as_admin(client, db_session)

    response = _upload_csv(client, VALID_CSV)

    assert response.status_code == 200
    assert response.json() == {"created_count": 2}
    stored_titles = db_session.execute(select(Recipe.title)).scalars().all()
    assert set(stored_titles) == {"Curry", "Salade"}


def test_import_reports_row_errors_and_imports_nothing(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)
    csv_with_bad_row = "title,ingredients\nCurry,lentilles\n,tomates\n"

    response = _upload_csv(client, csv_with_bad_row)

    assert response.status_code == 400
    errors = response.json()["detail"]
    assert errors == [{"row": 3, "message": "la colonne 'title' est obligatoire"}]
    assert db_session.execute(select(Recipe)).scalars().all() == []


def test_export_requires_admin_session(client: TestClient) -> None:
    response = client.get("/admin/recipes/export")

    assert response.status_code == 401


def test_export_returns_csv_attachment_for_admin(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)
    _upload_csv(client, VALID_CSV)

    response = client.get("/admin/recipes/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert "recipes.csv" in response.headers["content-disposition"]
    body = response.content.decode("utf-8-sig")
    assert body.splitlines()[0].startswith("title,ingredients,allergens")
    assert "Curry" in body
    assert "Salade" in body
