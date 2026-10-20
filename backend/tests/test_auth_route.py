import logging
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from veggie_app.config import settings
from veggie_app.services import auth_service


def test_login_succeeds_and_sets_cookie(client: TestClient, db_session: Session) -> None:
    auth_service.register_user(
        db_session, "admin@example.com", "correct horse battery", is_admin=True
    )
    db_session.flush()

    response = client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "correct horse battery"}
    )

    assert response.status_code == 200
    assert response.json() == {"email": "admin@example.com", "is_admin": True}
    assert auth_service.SESSION_COOKIE_NAME in response.cookies


def test_session_cookie_is_not_secure_in_development(
    client: TestClient, db_session: Session
) -> None:
    auth_service.register_user(db_session, "person@example.com", "correct horse battery")
    db_session.flush()

    response = client.post(
        "/auth/login", json={"email": "person@example.com", "password": "correct horse battery"}
    )

    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "secure" not in set_cookie


def test_session_cookie_is_secure_in_production(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    auth_service.register_user(db_session, "person@example.com", "correct horse battery")
    db_session.flush()

    login_response = client.post(
        "/auth/login", json={"email": "person@example.com", "password": "correct horse battery"}
    )
    # The test client (plain http) won't resend a Secure cookie on its own,
    # so hand it back explicitly. The deleting Set-Cookie on logout must
    # carry the same Secure flag.
    client.cookies.set(
        auth_service.SESSION_COOKIE_NAME,
        login_response.cookies[auth_service.SESSION_COOKIE_NAME],
    )
    logout_response = client.post("/auth/logout")

    assert "secure" in login_response.headers["set-cookie"].lower()
    assert "secure" in logout_response.headers["set-cookie"].lower()


def test_cors_allows_configured_origin_with_credentials(client: TestClient) -> None:
    response = client.options(
        "/auth/login",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_rejects_unlisted_origin(client: TestClient) -> None:
    response = client.options(
        "/auth/login",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_login_fails_with_wrong_password(client: TestClient, db_session: Session) -> None:
    auth_service.register_user(
        db_session, "admin@example.com", "correct horse battery", is_admin=True
    )
    db_session.flush()

    response = client.post("/auth/login", json={"email": "admin@example.com", "password": "wrong"})

    assert response.status_code == 401


def test_login_fails_for_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )

    assert response.status_code == 401


def test_signup_creates_non_admin_user_and_logs_in(client: TestClient) -> None:
    response = client.post(
        "/auth/signup", json={"email": "person@example.com", "password": "correct horse battery"}
    )

    assert response.status_code == 200
    assert response.json() == {"email": "person@example.com", "is_admin": False}
    assert auth_service.SESSION_COOKIE_NAME in response.cookies


def test_signup_rejects_duplicate_email(client: TestClient, db_session: Session) -> None:
    auth_service.register_user(db_session, "person@example.com", "correct horse battery")
    db_session.flush()

    response = client.post(
        "/auth/signup", json={"email": "person@example.com", "password": "another password"}
    )

    assert response.status_code == 409


def test_me_returns_current_user_when_logged_in(client: TestClient, db_session: Session) -> None:
    auth_service.register_user(
        db_session, "admin@example.com", "correct horse battery", is_admin=True
    )
    db_session.flush()
    client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "correct horse battery"}
    )

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {"email": "admin@example.com", "is_admin": True}


def test_me_returns_401_without_session(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_succeeds_for_non_admin_user(client: TestClient, db_session: Session) -> None:
    auth_service.register_user(db_session, "person@example.com", "correct horse battery")
    db_session.flush()
    client.post(
        "/auth/login", json={"email": "person@example.com", "password": "correct horse battery"}
    )

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {"email": "person@example.com", "is_admin": False}


def test_logout_clears_session(client: TestClient, db_session: Session) -> None:
    auth_service.register_user(
        db_session, "admin@example.com", "correct horse battery", is_admin=True
    )
    db_session.flush()
    client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "correct horse battery"}
    )

    logout_response = client.post("/auth/logout")
    me_response = client.get("/auth/me")

    assert logout_response.status_code == 200
    assert me_response.status_code == 401


def test_password_reset_request_and_confirm_round_trip(
    client: TestClient, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    auth_service.register_user(db_session, "person@example.com", "old password")
    db_session.flush()

    with caplog.at_level(logging.WARNING, logger=auth_service.__name__):
        request_response = client.post(
            "/auth/password-reset/request", json={"email": "person@example.com"}
        )
    assert request_response.status_code == 200
    # The token reaches the owner out of band (the server log, for now) —
    # never the HTTP caller.
    match = re.search(r"token=(\S+)", caplog.text)
    assert match is not None
    token = match.group(1)

    confirm_response = client.post(
        "/auth/password-reset/confirm", json={"token": token, "new_password": "new password"}
    )
    assert confirm_response.status_code == 200

    login_response = client.post(
        "/auth/login", json={"email": "person@example.com", "password": "new password"}
    )
    assert login_response.status_code == 200


def test_password_reset_request_never_returns_the_token(
    client: TestClient, db_session: Session
) -> None:
    # Regression guard: returning the token let anyone reset any account's
    # password (the admin's included) knowing only its email.
    auth_service.register_user(db_session, "person@example.com", "old password")
    db_session.flush()

    response = client.post("/auth/password-reset/request", json={"email": "person@example.com"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_password_reset_request_does_not_leak_unknown_email(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger=auth_service.__name__):
        response = client.post("/auth/password-reset/request", json={"email": "nobody@example.com"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "token=" not in caplog.text


def test_password_reset_confirm_rejects_invalid_token(client: TestClient) -> None:
    response = client.post(
        "/auth/password-reset/confirm",
        json={"token": "not-a-real-token", "new_password": "new password"},
    )

    assert response.status_code == 400


def test_update_account_changes_password(client: TestClient, db_session: Session) -> None:
    auth_service.register_user(db_session, "person@example.com", "old password")
    db_session.flush()
    client.post("/auth/login", json={"email": "person@example.com", "password": "old password"})

    response = client.patch("/auth/account", json={"password": "new password"})

    assert response.status_code == 200
    login_response = client.post(
        "/auth/login", json={"email": "person@example.com", "password": "new password"}
    )
    assert login_response.status_code == 200


def test_update_account_requires_session(client: TestClient) -> None:
    response = client.patch("/auth/account", json={"password": "new password"})

    assert response.status_code == 401


def test_delete_account_removes_session(client: TestClient, db_session: Session) -> None:
    auth_service.register_user(db_session, "person@example.com", "password")
    db_session.flush()
    client.post("/auth/login", json={"email": "person@example.com", "password": "password"})

    response = client.delete("/auth/account")
    me_response = client.get("/auth/me")

    assert response.status_code == 200
    assert me_response.status_code == 401
