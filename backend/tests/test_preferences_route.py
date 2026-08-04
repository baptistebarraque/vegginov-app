from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from veggie_app.services import auth_service


def _signup_and_login(
    client: TestClient, db_session: Session, email: str = "person@example.com"
) -> None:
    auth_service.register_user(db_session, email, "password")
    db_session.flush()
    client.post("/auth/login", json={"email": email, "password": "password"})


def test_get_preferences_requires_session(client: TestClient) -> None:
    response = client.get("/preferences")

    assert response.status_code == 401


def test_get_preferences_defaults_to_empty_before_any_put(
    client: TestClient, db_session: Session
) -> None:
    _signup_and_login(client, db_session)

    response = client.get("/preferences")

    assert response.status_code == 200
    assert response.json() == {
        "calorie_orientation": None,
        "diet": None,
        "allergens": [],
        "price_range": None,
    }


def test_put_preferences_then_get_reflects_saved_values(
    client: TestClient, db_session: Session
) -> None:
    _signup_and_login(client, db_session)

    put_response = client.put(
        "/preferences",
        json={
            "calorie_orientation": "low",
            "diet": "vegan",
            "allergens": ["gluten", "lactose"],
            "price_range": 2,
        },
    )
    assert put_response.status_code == 200
    assert put_response.json() == {
        "calorie_orientation": "low",
        "diet": "vegan",
        "allergens": ["gluten", "lactose"],
        "price_range": 2,
    }

    get_response = client.get("/preferences")
    assert get_response.json() == put_response.json()


def test_put_preferences_rejects_invalid_diet(client: TestClient, db_session: Session) -> None:
    _signup_and_login(client, db_session)

    response = client.put(
        "/preferences",
        json={
            "calorie_orientation": None,
            "diet": "carnivore",
            "allergens": [],
            "price_range": None,
        },
    )

    assert response.status_code == 400


def test_put_preferences_requires_session(client: TestClient) -> None:
    response = client.put(
        "/preferences",
        json={"calorie_orientation": None, "diet": None, "allergens": [], "price_range": None},
    )

    assert response.status_code == 401
