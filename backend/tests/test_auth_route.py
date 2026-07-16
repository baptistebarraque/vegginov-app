from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from veggie_app.models.user import User
from veggie_app.services import auth_service


def test_login_succeeds_and_sets_cookie(client: TestClient, db_session: Session) -> None:
    auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")
    db_session.flush()

    response = client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "correct horse battery"}
    )

    assert response.status_code == 200
    assert response.json() == {"email": "admin@example.com"}
    assert auth_service.SESSION_COOKIE_NAME in response.cookies


def test_login_fails_with_wrong_password(client: TestClient, db_session: Session) -> None:
    auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")
    db_session.flush()

    response = client.post("/auth/login", json={"email": "admin@example.com", "password": "wrong"})

    assert response.status_code == 401


def test_login_fails_for_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )

    assert response.status_code == 401


def test_me_returns_current_admin_when_logged_in(client: TestClient, db_session: Session) -> None:
    auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")
    db_session.flush()
    client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "correct horse battery"}
    )

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {"email": "admin@example.com"}


def test_me_returns_401_without_session(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_logout_clears_session(client: TestClient, db_session: Session) -> None:
    auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")
    db_session.flush()
    client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "correct horse battery"}
    )

    logout_response = client.post("/auth/logout")
    me_response = client.get("/auth/me")

    assert logout_response.status_code == 200
    assert me_response.status_code == 401


def test_me_returns_403_for_non_admin_user(client: TestClient, db_session: Session) -> None:
    user = User(email="user@example.com", password_hash="irrelevant", is_admin=False)
    db_session.add(user)
    db_session.flush()
    raw_token = auth_service.create_session(db_session, user)
    client.cookies.set(auth_service.SESSION_COOKIE_NAME, raw_token)

    response = client.get("/auth/me")

    assert response.status_code == 403
