from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from veggie_app.matching.embeddings import EMBEDDING_DIM
from veggie_app.models.recipe import Recipe
from veggie_app.services import auth_service


def test_post_suggestions_returns_matching_recipes(client: TestClient, db_session: Session) -> None:
    db_session.add(
        Recipe(
            title="Curry de lentilles",
            ingredients=[
                {"name": "lentilles", "quantity": None},
                {"name": "curry", "quantity": None},
            ],
            allergens=[],
            embedding=[0.1] * EMBEDDING_DIM,
        )
    )
    db_session.flush()

    response = client.post(
        "/suggestions", json={"title": "Curry de poulet", "ingredients": ["poulet"]}
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["suggestions"]) == 1
    assert body["suggestions"][0]["title"] == "Curry de lentilles"
    assert body["suggestions"][0]["ingredients"] == [
        {"name": "lentilles", "quantity": None},
        {"name": "curry", "quantity": None},
    ]
    assert body["suggestions"][0]["image_url"] is None
    assert body["suggestions"][0]["is_watchlisted"] is False
    assert body["suggestions"][0]["is_liked"] is False
    assert body["suggestions"][0]["like_count"] == 0


def test_post_suggestions_empty_db_returns_empty_list(client: TestClient) -> None:
    response = client.post("/suggestions", json={"title": "Curry de poulet", "ingredients": []})

    assert response.status_code == 200
    assert response.json() == {"suggestions": []}


def test_post_suggestions_requires_title(client: TestClient) -> None:
    response = client.post("/suggestions", json={"ingredients": ["poulet"]})

    assert response.status_code == 422


def test_post_suggestions_excludes_recipe_matching_logged_in_users_allergen(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        Recipe(
            title="Curry de lentilles au gluten",
            ingredients=[{"name": "lentilles", "quantity": None}],
            allergens=["gluten"],
            embedding=[0.1] * EMBEDDING_DIM,
        )
    )
    db_session.flush()
    auth_service.register_user(db_session, "person@example.com", "password")
    db_session.flush()
    client.post("/auth/login", json={"email": "person@example.com", "password": "password"})
    client.put(
        "/preferences",
        json={
            "calorie_orientation": None,
            "diet": None,
            "allergens": ["gluten"],
            "price_range": None,
        },
    )

    response = client.post("/suggestions", json={"title": "Curry de poulet", "ingredients": []})

    assert response.status_code == 200
    assert response.json() == {"suggestions": []}


def test_post_suggestions_ignore_preferences_includes_the_recipe_back(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        Recipe(
            title="Curry de lentilles au gluten",
            ingredients=[{"name": "lentilles", "quantity": None}],
            allergens=["gluten"],
            embedding=[0.1] * EMBEDDING_DIM,
        )
    )
    db_session.flush()
    auth_service.register_user(db_session, "person@example.com", "password")
    db_session.flush()
    client.post("/auth/login", json={"email": "person@example.com", "password": "password"})
    client.put(
        "/preferences",
        json={
            "calorie_orientation": None,
            "diet": None,
            "allergens": ["gluten"],
            "price_range": None,
        },
    )

    response = client.post(
        "/suggestions",
        json={"title": "Curry de poulet", "ingredients": [], "ignore_preferences": True},
    )

    assert response.status_code == 200
    assert len(response.json()["suggestions"]) == 1


def test_post_suggestions_marks_watchlisted_recipe_for_logged_in_user(
    client: TestClient, db_session: Session
) -> None:
    recipe = Recipe(
        title="Curry de lentilles",
        ingredients=[{"name": "lentilles", "quantity": None}],
        allergens=[],
        embedding=[0.1] * EMBEDDING_DIM,
    )
    db_session.add(recipe)
    db_session.flush()
    auth_service.register_user(db_session, "person@example.com", "password")
    db_session.flush()
    client.post("/auth/login", json={"email": "person@example.com", "password": "password"})
    client.post(f"/watchlist/{recipe.id}")

    response = client.post("/suggestions", json={"title": "Curry de poulet", "ingredients": []})

    assert response.status_code == 200
    assert response.json()["suggestions"][0]["is_watchlisted"] is True


def test_post_suggestions_marks_liked_recipe_and_counts_for_logged_in_user(
    client: TestClient, db_session: Session
) -> None:
    recipe = Recipe(
        title="Curry de lentilles",
        ingredients=[{"name": "lentilles", "quantity": None}],
        allergens=[],
        embedding=[0.1] * EMBEDDING_DIM,
    )
    db_session.add(recipe)
    db_session.flush()
    auth_service.register_user(db_session, "person@example.com", "password")
    db_session.flush()
    client.post("/auth/login", json={"email": "person@example.com", "password": "password"})
    client.post(f"/likes/{recipe.id}")

    response = client.post("/suggestions", json={"title": "Curry de poulet", "ingredients": []})

    assert response.status_code == 200
    assert response.json()["suggestions"][0]["is_liked"] is True
    assert response.json()["suggestions"][0]["like_count"] == 1


def test_post_suggestions_shows_public_like_count_to_anonymous(
    client: TestClient, db_session: Session
) -> None:
    recipe = Recipe(
        title="Curry de lentilles",
        ingredients=[{"name": "lentilles", "quantity": None}],
        allergens=[],
        embedding=[0.1] * EMBEDDING_DIM,
    )
    db_session.add(recipe)
    db_session.flush()
    # A logged-in user likes the recipe, then logs out.
    auth_service.register_user(db_session, "person@example.com", "password")
    db_session.flush()
    client.post("/auth/login", json={"email": "person@example.com", "password": "password"})
    client.post(f"/likes/{recipe.id}")
    client.post("/auth/logout")

    response = client.post("/suggestions", json={"title": "Curry de poulet", "ingredients": []})

    assert response.status_code == 200
    # Count is public — visible even though the caller is anonymous — but the
    # per-user liked flag is not.
    assert response.json()["suggestions"][0]["like_count"] == 1
    assert response.json()["suggestions"][0]["is_liked"] is False


def test_post_suggestions_anonymous_ignores_allergens(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        Recipe(
            title="Curry de lentilles au gluten",
            ingredients=[{"name": "lentilles", "quantity": None}],
            allergens=["gluten"],
            embedding=[0.1] * EMBEDDING_DIM,
        )
    )
    db_session.flush()

    response = client.post("/suggestions", json={"title": "Curry de poulet", "ingredients": []})

    assert response.status_code == 200
    assert len(response.json()["suggestions"]) == 1
