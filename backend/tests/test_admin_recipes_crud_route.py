import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.models.user import User
from veggie_app.services import auth_service, image_service, recipe_service


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


def _create_recipe(db_session: Session, **overrides) -> Recipe:
    defaults = {
        "title": "Curry de lentilles",
        "ingredients": [{"name": "lentilles", "quantity": None}],
        "allergens": [],
        "embedding": [0.0] * EMBEDDING_DIM,
    }
    defaults.update(overrides)
    recipe = Recipe(**defaults)
    db_session.add(recipe)
    db_session.flush()
    return recipe


# --- GET /admin/recipes (list) ---


def test_list_recipes_requires_admin_session(client: TestClient) -> None:
    assert client.get("/admin/recipes").status_code == 401


def test_list_recipes_rejects_non_admin(client: TestClient, db_session: Session) -> None:
    user = User(email="user@example.com", password_hash="irrelevant", is_admin=False)
    db_session.add(user)
    db_session.flush()
    raw_token = auth_service.create_session(db_session, user)
    client.cookies.set(auth_service.SESSION_COOKIE_NAME, raw_token)

    assert client.get("/admin/recipes").status_code == 403


def test_list_recipes_returns_titles_and_image_urls(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)
    _create_recipe(db_session, title="Salade de quinoa")
    _create_recipe(db_session, title="Curry de lentilles", image_filename="abc.png")

    response = client.get("/admin/recipes")

    assert response.status_code == 200
    body = response.json()
    assert {item["title"] for item in body} == {"Salade de quinoa", "Curry de lentilles"}
    curry = next(item for item in body if item["title"] == "Curry de lentilles")
    assert curry["image_url"] == "/media/abc.png"


# --- GET /admin/recipes/{id} (detail) ---


def test_get_recipe_requires_admin_session(client: TestClient, db_session: Session) -> None:
    recipe = _create_recipe(db_session)

    assert client.get(f"/admin/recipes/{recipe.id}").status_code == 401


def test_get_recipe_returns_404_for_missing_recipe(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)

    assert client.get("/admin/recipes/999999").status_code == 404


def test_get_recipe_returns_full_detail(client: TestClient, db_session: Session) -> None:
    _login_as_admin(client, db_session)
    recipe = _create_recipe(
        db_session,
        title="Curry de lentilles",
        ingredients=[{"name": "lentilles", "quantity": "200g"}],
        servings=4,
    )

    response = client.get(f"/admin/recipes/{recipe.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Curry de lentilles"
    assert body["ingredients"] == [{"name": "lentilles", "quantity": "200g"}]
    assert body["servings"] == 4


# --- PUT /admin/recipes/{id} (update) ---


def test_update_recipe_requires_admin_session(client: TestClient, db_session: Session) -> None:
    recipe = _create_recipe(db_session)

    response = client.put(
        f"/admin/recipes/{recipe.id}",
        data={"title": "Nouveau titre", "ingredients": _ingredients_field([{"name": "laitue"}])},
    )

    assert response.status_code == 401


def test_update_recipe_returns_404_for_missing_recipe(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)

    response = client.put(
        "/admin/recipes/999999",
        data={"title": "Nouveau titre", "ingredients": _ingredients_field([{"name": "laitue"}])},
    )

    assert response.status_code == 404


def test_update_recipe_persists_changes_and_recomputes_embedding(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _login_as_admin(client, db_session)
    recipe = _create_recipe(db_session, title="Salade", ingredients=[{"name": "laitue"}])
    monkeypatch.setattr(recipe_service, "embed_text", lambda text: [1.0] * EMBEDDING_DIM)

    response = client.put(
        f"/admin/recipes/{recipe.id}",
        data={
            "title": "Grande salade",
            "ingredients": _ingredients_field(
                [{"name": "laitue", "quantity": "200g"}, {"name": "tomate", "quantity": "2"}]
            ),
            "servings": 2,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Grande salade"
    assert body["ingredients"] == [
        {"name": "laitue", "quantity": "200g"},
        {"name": "tomate", "quantity": "2"},
    ]
    assert body["servings"] == 2

    fetched = db_session.get(Recipe, recipe.id)
    assert fetched is not None
    assert fetched.title == "Grande salade"
    assert list(fetched.embedding) == [1.0] * EMBEDDING_DIM


def test_update_recipe_rejects_missing_quantity_when_servings_set(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)
    recipe = _create_recipe(db_session)

    response = client.put(
        f"/admin/recipes/{recipe.id}",
        data={
            "title": "Salade",
            "ingredients": _ingredients_field([{"name": "laitue"}]),
            "servings": 2,
        },
    )

    assert response.status_code == 400
    fetched = db_session.get(Recipe, recipe.id)
    assert fetched is not None
    assert fetched.servings is None  # unchanged


def test_update_recipe_replaces_image_and_deletes_old_file(
    client: TestClient, db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(image_service.settings, "upload_dir", tmp_path / "uploads")
    _login_as_admin(client, db_session)
    old_filename = image_service.save_recipe_image("old.png", b"old-bytes")
    recipe = _create_recipe(db_session, image_filename=old_filename)

    response = client.put(
        f"/admin/recipes/{recipe.id}",
        data={"title": "Salade", "ingredients": _ingredients_field([{"name": "laitue"}])},
        files={"image": ("new.png", b"new-bytes", "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["image_url"] is not None
    assert body["image_url"] != f"/media/{old_filename}"
    assert not (image_service.settings.upload_dir / old_filename).exists()


def test_update_recipe_removes_image_when_requested(
    client: TestClient, db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(image_service.settings, "upload_dir", tmp_path / "uploads")
    _login_as_admin(client, db_session)
    old_filename = image_service.save_recipe_image("old.png", b"old-bytes")
    recipe = _create_recipe(db_session, image_filename=old_filename)

    response = client.put(
        f"/admin/recipes/{recipe.id}",
        data={
            "title": "Salade",
            "ingredients": _ingredients_field([{"name": "laitue"}]),
            "remove_image": "true",
        },
    )

    assert response.status_code == 200
    assert response.json()["image_url"] is None
    assert not (image_service.settings.upload_dir / old_filename).exists()
    fetched = db_session.get(Recipe, recipe.id)
    assert fetched is not None
    assert fetched.image_filename is None


# --- DELETE /admin/recipes/{id} ---


def test_delete_recipe_requires_admin_session(client: TestClient, db_session: Session) -> None:
    recipe = _create_recipe(db_session)

    assert client.delete(f"/admin/recipes/{recipe.id}").status_code == 401


def test_delete_recipe_returns_404_for_missing_recipe(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)

    assert client.delete("/admin/recipes/999999").status_code == 404


def test_delete_recipe_removes_row_and_image_file(
    client: TestClient, db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(image_service.settings, "upload_dir", tmp_path / "uploads")
    _login_as_admin(client, db_session)
    filename = image_service.save_recipe_image("photo.png", b"bytes")
    recipe = _create_recipe(db_session, image_filename=filename)
    recipe_id = recipe.id

    response = client.delete(f"/admin/recipes/{recipe_id}")

    assert response.status_code == 204
    assert db_session.get(Recipe, recipe_id) is None
    assert not (image_service.settings.upload_dir / filename).exists()
