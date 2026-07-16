from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from veggie_app.models.admin_session import AdminSession
from veggie_app.services import auth_service


def test_create_admin_hashes_password_and_sets_is_admin(db_session: Session) -> None:
    user = auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")

    assert user.email == "admin@example.com"
    assert user.is_admin is True
    assert user.password_hash != "correct horse battery"


def test_authenticate_succeeds_with_correct_password(db_session: Session) -> None:
    auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")

    user = auth_service.authenticate(db_session, "admin@example.com", "correct horse battery")

    assert user is not None
    assert user.email == "admin@example.com"


def test_authenticate_fails_with_wrong_password(db_session: Session) -> None:
    auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")

    user = auth_service.authenticate(db_session, "admin@example.com", "wrong password")

    assert user is None


def test_authenticate_fails_for_unknown_email(db_session: Session) -> None:
    user = auth_service.authenticate(db_session, "nobody@example.com", "whatever")

    assert user is None


def test_create_session_then_resolve_session_returns_user(db_session: Session) -> None:
    admin = auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")

    raw_token = auth_service.create_session(db_session, admin)
    resolved = auth_service.resolve_session(db_session, raw_token)

    assert resolved is not None
    assert resolved.id == admin.id


def test_resolve_session_returns_none_for_unknown_token(db_session: Session) -> None:
    assert auth_service.resolve_session(db_session, "not-a-real-token") is None


def test_resolve_session_returns_none_for_expired_session(db_session: Session) -> None:
    admin = auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")
    db_session.add(
        AdminSession(
            user_id=admin.id,
            token_hash=auth_service._hash_token("expired-token"),
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
    )
    db_session.flush()

    assert auth_service.resolve_session(db_session, "expired-token") is None


def test_delete_session_invalidates_it(db_session: Session) -> None:
    admin = auth_service.create_admin(db_session, "admin@example.com", "correct horse battery")
    raw_token = auth_service.create_session(db_session, admin)

    auth_service.delete_session(db_session, raw_token)

    assert auth_service.resolve_session(db_session, raw_token) is None
