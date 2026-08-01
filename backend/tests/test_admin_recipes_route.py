import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.models.user import User
from veggie_app.services import auth_service, recipe_service


def _ingredients_field(entries: list[dict]) -> str:
    return json.dumps(entries)


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
    response = client.post(
        "/admin/recipes",
        data={"title": "Salade", "ingredients": _ingredients_field([{"name": "laitue"}])},
    )

    assert response.status_code == 401


def test_create_recipe_rejects_non_admin(client: TestClient, db_session: Session) -> None:
    user = User(email="user@example.com", password_hash="irrelevant", is_admin=False)
    db_session.add(user)
    db_session.flush()
    raw_token = auth_service.create_session(db_session, user)
    client.cookies.set(auth_service.SESSION_COOKIE_NAME, raw_token)

    response = client.post(
        "/admin/recipes",
        data={"title": "Salade", "ingredients": _ingredients_field([{"name": "laitue"}])},
    )

    assert response.status_code == 403


def test_create_recipe_succeeds_for_admin(client: TestClient, db_session: Session) -> None:
    _login_as_admin(client, db_session)

    response = client.post(
        "/admin/recipes",
        data={
            "title": "Curry de lentilles corail",
            "ingredients": _ingredients_field(
                [
                    {"name": "lentilles corail", "quantity": "200g"},
                    {"name": "lait de coco", "quantity": "200ml"},
                    {"name": "curry", "quantity": "1 cuillère à soupe"},
                ]
            ),
            "allergens": ["gluten"],
            "prep_time_minutes": 25,
            "servings": 4,
            "protein_source": "lentilles corail",
            "protein_grams": 15.0,
            "instructions": ["Faire chauffer le lait de coco", "Ajouter les lentilles et le curry"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Curry de lentilles corail"
    assert body["ingredients"] == [
        {"name": "lentilles corail", "quantity": "200g"},
        {"name": "lait de coco", "quantity": "200ml"},
        {"name": "curry", "quantity": "1 cuillère à soupe"},
    ]
    assert body["allergens"] == ["gluten"]
    assert body["prep_time_minutes"] == 25
    assert body["servings"] == 4
    assert body["protein_source"] == "lentilles corail"
    assert body["protein_grams"] == 15.0
    assert body["instructions"] == [
        "Faire chauffer le lait de coco",
        "Ajouter les lentilles et le curry",
    ]
    assert body["image_url"] is None

    fetched = db_session.get(Recipe, body["id"])
    assert fetched is not None
    assert list(fetched.embedding) == [0.0] * EMBEDDING_DIM


def test_create_recipe_allows_missing_quantity_without_servings(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)

    response = client.post(
        "/admin/recipes",
        data={"title": "Salade", "ingredients": _ingredients_field([{"name": "laitue"}])},
    )

    assert response.status_code == 200
    assert response.json()["ingredients"] == [{"name": "laitue", "quantity": None}]


def test_create_recipe_rejects_missing_quantity_when_servings_set(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)

    response = client.post(
        "/admin/recipes",
        data={
            "title": "Salade",
            "ingredients": _ingredients_field([{"name": "laitue"}]),
            "servings": 2,
        },
    )

    assert response.status_code == 400
    assert db_session.query(Recipe).count() == 0


def test_create_recipe_rejects_malformed_ingredients_json(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)

    response = client.post(
        "/admin/recipes",
        data={"title": "Salade", "ingredients": "not-json"},
    )

    assert response.status_code == 400


def test_create_recipe_with_image_stores_and_returns_url(
    client: TestClient, db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from veggie_app.services import image_service

    monkeypatch.setattr(image_service.settings, "upload_dir", tmp_path / "uploads")
    _login_as_admin(client, db_session)

    response = client.post(
        "/admin/recipes",
        data={"title": "Salade", "ingredients": _ingredients_field([{"name": "laitue"}])},
        files={"image": ("photo.png", b"fake-png-bytes", "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["image_url"] is not None
    assert body["image_url"].startswith("/media/")
    assert body["image_url"].endswith(".png")

    fetched = db_session.get(Recipe, body["id"])
    assert fetched is not None
    assert fetched.image_filename is not None
    assert (image_service.settings.upload_dir / fetched.image_filename).read_bytes() == (
        b"fake-png-bytes"
    )


def test_create_recipe_rejects_unknown_protein_source(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)

    response = client.post(
        "/admin/recipes",
        data={
            "title": "Salade",
            "ingredients": _ingredients_field([{"name": "laitue"}]),
            "protein_source": "steak",
        },
    )

    assert response.status_code == 400
    assert db_session.query(Recipe).count() == 0


def test_protein_sources_requires_admin_session(client: TestClient) -> None:
    assert client.get("/admin/protein-sources").status_code == 401


def test_protein_sources_returns_known_vocabulary(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)

    response = client.get("/admin/protein-sources")

    assert response.status_code == 200
    options = response.json()
    assert "tofu" in options
    assert "seitan" in options


def test_create_recipe_rejects_invalid_image_extension(
    client: TestClient, db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from veggie_app.services import image_service

    monkeypatch.setattr(image_service.settings, "upload_dir", tmp_path / "uploads")
    _login_as_admin(client, db_session)

    response = client.post(
        "/admin/recipes",
        data={"title": "Salade", "ingredients": _ingredients_field([{"name": "laitue"}])},
        files={"image": ("photo.gif", b"fake-bytes", "image/gif")},
    )

    assert response.status_code == 400
