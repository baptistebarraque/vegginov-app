from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.models.user import User
from veggie_app.services import (
    auth_service,
    like_service,
    preference_service,
    watchlist_service,
)


def _login_as_admin(client: TestClient, db_session: Session) -> User:
    admin = auth_service.register_user(
        db_session, "admin@example.com", "correct horse battery", is_admin=True
    )
    db_session.flush()
    client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "correct horse battery"}
    )
    return admin


def _login_as_user(client: TestClient, db_session: Session) -> User:
    user = auth_service.register_user(db_session, "person@example.com", "password")
    db_session.flush()
    client.post("/auth/login", json={"email": "person@example.com", "password": "password"})
    return user


def _add_user(db_session: Session, email: str) -> User:
    user = auth_service.register_user(db_session, email, "password")
    db_session.flush()
    return user


def _add_recipe(db_session: Session, title: str = "Curry de lentilles") -> Recipe:
    recipe = Recipe(title=title, ingredients=[], allergens=[], embedding=[0.1] * EMBEDDING_DIM)
    db_session.add(recipe)
    db_session.flush()
    return recipe


def test_list_users_requires_a_session(client: TestClient) -> None:
    response = client.get("/admin/users")

    assert response.status_code == 401


def test_list_users_rejects_a_non_admin(client: TestClient, db_session: Session) -> None:
    _login_as_user(client, db_session)

    response = client.get("/admin/users")

    assert response.status_code == 403


def test_list_users_returns_every_account_newest_first(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)
    _add_user(db_session, "person@example.com")

    response = client.get("/admin/users")

    assert response.status_code == 200
    users = response.json()
    assert [user["email"] for user in users] == ["person@example.com", "admin@example.com"]
    assert users[1]["is_admin"] is True
    assert users[0]["is_admin"] is False


def test_list_users_never_exposes_password_hashes(client: TestClient, db_session: Session) -> None:
    _login_as_admin(client, db_session)

    response = client.get("/admin/users")

    assert response.status_code == 200
    assert "password_hash" not in response.text


def test_list_users_includes_counts_and_preference_flag(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)
    person = _add_user(db_session, "person@example.com")
    curry = _add_recipe(db_session)
    watchlist_service.add(db_session, person.id, curry.id)
    like_service.add(db_session, person.id, curry.id)
    preference_service.upsert_preferences(
        db_session,
        person.id,
        calorie_orientation="low",
        diet=None,
        allergens=[],
        price_range=None,
    )

    response = client.get("/admin/users")

    listed = {user["email"]: user for user in response.json()}
    assert listed["person@example.com"]["watchlist_count"] == 1
    assert listed["person@example.com"]["like_count"] == 1
    assert listed["person@example.com"]["has_preferences"] is True
    assert listed["admin@example.com"]["has_preferences"] is False
    assert listed["person@example.com"]["created_at"] is not None


def test_get_user_requires_admin(client: TestClient, db_session: Session) -> None:
    user = _login_as_user(client, db_session)

    response = client.get(f"/admin/users/{user.id}")

    assert response.status_code == 403


def test_get_user_returns_404_for_an_unknown_id(client: TestClient, db_session: Session) -> None:
    _login_as_admin(client, db_session)

    response = client.get("/admin/users/999999")

    assert response.status_code == 404


def test_get_user_returns_preferences_watchlist_and_likes(
    client: TestClient, db_session: Session
) -> None:
    _login_as_admin(client, db_session)
    person = _add_user(db_session, "person@example.com")
    curry = _add_recipe(db_session, "Curry de lentilles")
    dahl = _add_recipe(db_session, "Dahl de pois cassés")
    watchlist_service.add(db_session, person.id, curry.id)
    watchlist_service.update_entry(
        db_session, person.id, curry.id, notes="Pour dimanche", planned_for=None
    )
    like_service.add(db_session, person.id, dahl.id)
    preference_service.upsert_preferences(
        db_session,
        person.id,
        calorie_orientation="balanced",
        diet="vegetarian",
        allergens=["gluten", "arachide"],
        price_range=3,
    )

    response = client.get(f"/admin/users/{person.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "person@example.com"
    assert body["preferences"] == {
        "calorie_orientation": "balanced",
        "diet": "vegetarian",
        "allergens": ["gluten", "arachide"],
        "price_range": 3,
    }
    assert body["watchlist"] == [
        {
            "recipe_id": curry.id,
            "title": "Curry de lentilles",
            "image_url": None,
            "notes": "Pour dimanche",
            "planned_for": None,
        }
    ]
    assert body["likes"] == [
        {"recipe_id": dahl.id, "title": "Dahl de pois cassés", "image_url": None}
    ]
    assert body["watchlist_count"] == 1
    assert body["like_count"] == 1


def test_get_user_without_preferences_returns_null(client: TestClient, db_session: Session) -> None:
    _login_as_admin(client, db_session)
    person = _add_user(db_session, "person@example.com")

    response = client.get(f"/admin/users/{person.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["preferences"] is None
    assert body["has_preferences"] is False
    assert body["watchlist"] == []
    assert body["likes"] == []
