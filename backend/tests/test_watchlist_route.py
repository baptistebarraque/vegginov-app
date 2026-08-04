from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.services import auth_service


def _signup_and_login(
    client: TestClient, db_session: Session, email: str = "person@example.com"
) -> None:
    auth_service.register_user(db_session, email, "password")
    db_session.flush()
    client.post("/auth/login", json={"email": email, "password": "password"})


def _add_recipe(db_session: Session, title: str = "Curry de lentilles") -> Recipe:
    recipe = Recipe(title=title, ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    db_session.add(recipe)
    db_session.flush()
    return recipe


def test_list_watchlist_requires_session(client: TestClient) -> None:
    response = client.get("/watchlist")

    assert response.status_code == 401


def test_list_watchlist_starts_empty(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)

    response = client.get("/watchlist")

    assert response.status_code == 200
    assert response.json() == {"entries": []}


def test_add_then_list_returns_the_recipe(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)
    recipe = _add_recipe(db_session)

    add_response = client.post(f"/watchlist/{recipe.id}")
    assert add_response.status_code == 200
    assert add_response.json()["recipe_id"] == recipe.id
    assert add_response.json()["title"] == "Curry de lentilles"

    list_response = client.get("/watchlist")
    assert list_response.status_code == 200
    assert len(list_response.json()["entries"]) == 1
    assert list_response.json()["entries"][0]["recipe_id"] == recipe.id


def test_add_is_idempotent_over_http(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)
    recipe = _add_recipe(db_session)

    client.post(f"/watchlist/{recipe.id}")
    client.post(f"/watchlist/{recipe.id}")

    assert len(client.get("/watchlist").json()["entries"]) == 1


def test_add_unknown_recipe_returns_404(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)

    response = client.post("/watchlist/999999")

    assert response.status_code == 404


def test_add_requires_session(client: TestClient, db_session: Session) -> None:
    recipe = _add_recipe(db_session)

    response = client.post(f"/watchlist/{recipe.id}")

    assert response.status_code == 401


def test_delete_removes_the_entry(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)
    recipe = _add_recipe(db_session)
    client.post(f"/watchlist/{recipe.id}")

    delete_response = client.delete(f"/watchlist/{recipe.id}")

    assert delete_response.status_code == 204
    assert client.get("/watchlist").json()["entries"] == []


def test_delete_is_idempotent_when_not_watchlisted(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)
    recipe = _add_recipe(db_session)

    response = client.delete(f"/watchlist/{recipe.id}")

    assert response.status_code == 204


def test_patch_updates_notes_and_planned_for(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)
    recipe = _add_recipe(db_session)
    client.post(f"/watchlist/{recipe.id}")

    response = client.patch(
        f"/watchlist/{recipe.id}",
        json={"notes": "Pour dimanche", "planned_for": "2026-08-09"},
    )

    assert response.status_code == 200
    assert response.json()["notes"] == "Pour dimanche"
    assert response.json()["planned_for"] == "2026-08-09"


def test_patch_returns_404_when_not_watchlisted(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)
    recipe = _add_recipe(db_session)

    response = client.patch(f"/watchlist/{recipe.id}", json={"notes": "x", "planned_for": None})

    assert response.status_code == 404


def test_watchlist_is_scoped_per_user(client: TestClient, db_session: Session) -> None:
    recipe = _add_recipe(db_session)
    _signup_and_login(client, db_session, "a@example.com")
    client.post(f"/watchlist/{recipe.id}")
    client.post("/auth/logout")

    _signup_and_login(client, db_session, "b@example.com")
    response = client.get("/watchlist")

    assert response.json() == {"entries": []}
