import logging
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from veggie_app.models.password_reset_token import PasswordResetToken
from veggie_app.models.user_session import UserSession
from veggie_app.services import auth_service
from veggie_app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidEmailError,
    InvalidPasswordError,
    WrongCurrentPasswordError,
)


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


def test_deliver_reset_link_logs_a_frontend_link_carrying_the_token(
    db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "old password")

    with caplog.at_level(logging.WARNING, logger=auth_service.__name__):
        auth_service.deliver_reset_link(user, "raw-token-123")

    assert "person@example.com" in caplog.text
    assert "/reset-password/confirm?token=raw-token-123" in caplog.text


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
        db_session,
        user,
        current_password="old password",
        email="New@Example.com",
        password="new password",
    )

    assert user.email == "new@example.com"
    assert auth_service.authenticate(db_session, "new@example.com", "new password") is not None


def test_update_account_rejects_wrong_current_password(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "old password")

    with pytest.raises(WrongCurrentPasswordError):
        auth_service.update_account(
            db_session, user, current_password="wrong", email=None, password="new password"
        )

    assert auth_service.authenticate(db_session, "person@example.com", "old password") is not None


def test_update_account_rejects_duplicate_email(db_session: Session) -> None:
    auth_service.register_user(db_session, "taken@example.com", "password123")
    user = auth_service.register_user(db_session, "person@example.com", "password123")

    with pytest.raises(EmailAlreadyRegisteredError):
        auth_service.update_account(
            db_session,
            user,
            current_password="password123",
            email="taken@example.com",
            password=None,
        )


def test_password_change_revokes_other_sessions_but_keeps_current(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "old password")
    current_token = auth_service.create_session(db_session, user)
    stolen_token = auth_service.create_session(db_session, user)

    auth_service.update_account(
        db_session,
        user,
        current_password="old password",
        email=None,
        password="new password",
        current_raw_token=current_token,
    )

    assert auth_service.resolve_session(db_session, current_token) is not None
    assert auth_service.resolve_session(db_session, stolen_token) is None


def test_email_only_change_keeps_other_sessions(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "old password")
    other_token = auth_service.create_session(db_session, user)

    auth_service.update_account(
        db_session, user, current_password="old password", email="new@example.com", password=None
    )

    assert auth_service.resolve_session(db_session, other_token) is not None


def test_consume_reset_token_revokes_all_sessions_and_other_reset_tokens(
    db_session: Session,
) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "old password")
    session_token = auth_service.create_session(db_session, user)
    older_reset_token = auth_service.create_reset_token(db_session, user)
    reset_token = auth_service.create_reset_token(db_session, user)

    auth_service.consume_reset_token(db_session, reset_token, "new password")

    assert auth_service.resolve_session(db_session, session_token) is None
    assert auth_service.consume_reset_token(db_session, older_reset_token, "other password") is None


def test_consume_reset_token_rejects_weak_password_without_burning_the_token(
    db_session: Session,
) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "old password")
    reset_token = auth_service.create_reset_token(db_session, user)

    with pytest.raises(InvalidPasswordError):
        auth_service.consume_reset_token(db_session, reset_token, "short")

    assert auth_service.consume_reset_token(db_session, reset_token, "new password") is not None


@pytest.mark.parametrize(
    ("password", "message"),
    [("123456789", "au moins 10"), ("é" * 37, "trop long")],
)
def test_validate_new_password_enforces_length_bounds(password: str, message: str) -> None:
    with pytest.raises(InvalidPasswordError, match=message):
        auth_service.validate_new_password(password)


def test_validate_new_password_accepts_exactly_72_bytes() -> None:
    auth_service.validate_new_password("é" * 36)


@pytest.mark.parametrize("email", ["", "plain", "a@b", "a b@c.fr", "a@@b.fr", "x" * 250 + "@a.fr"])
def test_normalize_email_rejects_malformed_addresses(email: str) -> None:
    with pytest.raises(InvalidEmailError):
        auth_service.normalize_email(email)


def test_normalize_email_trims_and_lowercases() -> None:
    assert auth_service.normalize_email("  Jean.Dupont@Exemple.FR ") == "jean.dupont@exemple.fr"


def test_authenticate_returns_none_for_password_over_bcrypt_limit(db_session: Session) -> None:
    auth_service.register_user(db_session, "person@example.com", "correct horse battery")

    assert auth_service.authenticate(db_session, "person@example.com", "x" * 100) is None


def test_delete_account_removes_user_and_sessions(db_session: Session) -> None:
    user = auth_service.register_user(db_session, "person@example.com", "password123")
    raw_token = auth_service.create_session(db_session, user)

    auth_service.delete_account(db_session, user)
    db_session.flush()

    assert auth_service.resolve_session(db_session, raw_token) is None
