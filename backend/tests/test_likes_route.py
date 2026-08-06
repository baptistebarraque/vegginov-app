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


def test_list_likes_requires_session(client: TestClient) -> None:
    response = client.get("/likes")

    assert response.status_code == 401


def test_list_likes_starts_empty(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)

    response = client.get("/likes")

    assert response.status_code == 200
    assert response.json() == {"likes": []}


def test_like_then_list_returns_the_recipe_with_count(
    client: TestClient, db_session: Session
) -> None:
    _signup_and_login(client, db_session)
    recipe = _add_recipe(db_session)

    like_response = client.post(f"/likes/{recipe.id}")
    assert like_response.status_code == 200
    assert like_response.json() == {"recipe_id": recipe.id, "like_count": 1, "is_liked": True}

    list_response = client.get("/likes")
    assert list_response.status_code == 200
    likes = list_response.json()["likes"]
    assert len(likes) == 1
    assert likes[0]["recipe_id"] == recipe.id
    assert likes[0]["title"] == "Curry de lentilles"
    assert likes[0]["like_count"] == 1


def test_like_is_idempotent_over_http(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)
    recipe = _add_recipe(db_session)

    client.post(f"/likes/{recipe.id}")
    second = client.post(f"/likes/{recipe.id}")

    assert second.json()["like_count"] == 1
    assert len(client.get("/likes").json()["likes"]) == 1


def test_like_unknown_recipe_returns_404(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)

    response = client.post("/likes/999999")

    assert response.status_code == 404


def test_like_requires_session(client: TestClient, db_session: Session) -> None:
    recipe = _add_recipe(db_session)

    response = client.post(f"/likes/{recipe.id}")

    assert response.status_code == 401


def test_unlike_removes_the_like_and_returns_fresh_status(
    client: TestClient, db_session: Session
) -> None:
    _signup_and_login(client, db_session)
    recipe = _add_recipe(db_session)
    client.post(f"/likes/{recipe.id}")

    delete_response = client.delete(f"/likes/{recipe.id}")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"recipe_id": recipe.id, "like_count": 0, "is_liked": False}
    assert client.get("/likes").json()["likes"] == []


def test_unlike_is_idempotent_when_not_liked(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)
    recipe = _add_recipe(db_session)

    response = client.delete(f"/likes/{recipe.id}")

    assert response.status_code == 200
    assert response.json()["like_count"] == 0


def test_like_count_aggregates_across_users(client: TestClient, db_session: Session) -> None:
    recipe = _add_recipe(db_session)
    _signup_and_login(client, db_session, "a@example.com")
    client.post(f"/likes/{recipe.id}")
    client.post("/auth/logout")

    _signup_and_login(client, db_session, "b@example.com")
    response = client.post(f"/likes/{recipe.id}")

    assert response.json()["like_count"] == 2


def test_likes_list_is_scoped_per_user(client: TestClient, db_session: Session) -> None:
    recipe = _add_recipe(db_session)
    _signup_and_login(client, db_session, "a@example.com")
    client.post(f"/likes/{recipe.id}")
    client.post("/auth/logout")

    _signup_and_login(client, db_session, "b@example.com")
    response = client.get("/likes")

    assert response.json() == {"likes": []}
