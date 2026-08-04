from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from veggie_app.models.password_reset_token import PasswordResetToken
from veggie_app.models.user_session import UserSession
from veggie_app.services import auth_service
from veggie_app.services.auth_service import EmailAlreadyRegisteredError


def test_register_user_hashes_password_and_defaults_to_non_admin(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "correct horse battery")

    assert user.email == "person@example.com"
    assert user.is_admin is False
    assert user.password_hash != "correct horse battery"


def test_register_user_can_create_an_admin(db_session: Session) -> None:
    user = auth_service.register_user(
        db_session, "admin@example.com", "correct horse battery", is_admin=True
    )

    assert user.is_admin is True


def test_register_user_rejects_duplicate_email(db_session: Session) -> None:
    auth_service.register_user(db_session, "person@example.com", "correct horse battery")

    with pytest.raises(EmailAlreadyRegisteredError):
        auth_service.register_user(db_session, "person@example.com", "another password")


def test_authenticate_succeeds_with_correct_password(db_session: Session) -> None:
    auth_service.register_user(db_session, "person@example.com", "correct horse battery")

    user = auth_service.authenticate(db_session, "person@example.com", "correct horse battery")

    assert user is not None
    assert user.email == "person@example.com"


def test_authenticate_fails_with_wrong_password(db_session: Session) -> None:
    auth_service.register_user(db_session, "person@example.com", "correct horse battery")

    user = auth_service.authenticate(db_session, "person@example.com", "wrong password")

    assert user is None


def test_authenticate_fails_for_unknown_email(db_session: Session) -> None:
    user = auth_service.authenticate(db_session, "nobody@example.com", "whatever")

    assert user is None


def test_create_session_then_resolve_session_returns_user(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "correct horse battery")

    raw_token = auth_service.create_session(db_session, user)
    resolved = auth_service.resolve_session(db_session, raw_token)

    assert resolved is not None
    assert resolved.id == user.id


def test_resolve_session_returns_none_for_unknown_token(db_session: Session) -> None:
    assert auth_service.resolve_session(db_session, "not-a-real-token") is None


def test_resolve_session_returns_none_for_expired_session(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "correct horse battery")
    db_session.add(
        UserSession(
            user_id=user.id,
            token_hash=auth_service._hash_token("expired-token"),
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
    )
    db_session.flush()

    assert auth_service.resolve_session(db_session, "expired-token") is None


def test_delete_session_invalidates_it(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "correct horse battery")
    raw_token = auth_service.create_session(db_session, user)

    auth_service.delete_session(db_session, raw_token)

    assert auth_service.resolve_session(db_session, raw_token) is None


def test_create_reset_token_then_consume_updates_password(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "old password")

    raw_token = auth_service.create_reset_token(db_session, user)
    result = auth_service.consume_reset_token(db_session, raw_token, "new password")

    assert result is not None
    assert result.id == user.id
    assert auth_service.authenticate(db_session, "person@example.com", "new password") is not None
    assert auth_service.authenticate(db_session, "person@example.com", "old password") is None


def test_consume_reset_token_is_single_use(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "old password")
    raw_token = auth_service.create_reset_token(db_session, user)

    auth_service.consume_reset_token(db_session, raw_token, "new password")
    second_attempt = auth_service.consume_reset_token(db_session, raw_token, "another password")

    assert second_attempt is None


def test_consume_reset_token_returns_none_for_expired_token(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "old password")
    db_session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=auth_service._hash_token("expired-token"),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
    )
    db_session.flush()

    assert auth_service.consume_reset_token(db_session, "expired-token", "new password") is None


def test_update_account_changes_email_and_password(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "old password")

    auth_service.update_account(
        db_session, user, email="new@example.com", password="new password"
    )

    assert user.email == "new@example.com"
    assert auth_service.authenticate(db_session, "new@example.com", "new password") is not None


def test_update_account_rejects_duplicate_email(db_session: Session) -> None:
    auth_service.register_user(db_session, "taken@example.com", "password")
    user = auth_service.register_user(db_session, "person@example.com", "password")

    with pytest.raises(EmailAlreadyRegisteredError):
        auth_service.update_account(db_session, user, email="taken@example.com", password=None)


def test_delete_account_removes_user_and_sessions(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "password")
    raw_token = auth_service.create_session(db_session, user)

    auth_service.delete_account(db_session, user)
    db_session.flush()

    assert auth_service.resolve_session(db_session, raw_token) is None
