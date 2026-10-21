"""Authentication: password hashing, session issuing/validation, account
management.

resolve_session() is kept separate from require_user()/require_admin() so
session resolution can be tested directly with a DB session, without
needing to fabricate a FastAPI Request — require_user()/require_admin() are
the thin, FastAPI-specific wrappers routes actually depend on.
"""

import hashlib
import logging
import re
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from veggie_app.config import settings
from veggie_app.database import get_db
from veggie_app.models.password_reset_token import PasswordResetToken
from veggie_app.models.user import User
from veggie_app.models.user_session import UserSession

SESSION_COOKIE_NAME = "session_token"
SESSION_DURATION = timedelta(days=7)
RESET_TOKEN_DURATION = timedelta(hours=1)
MIN_PASSWORD_LENGTH = 10
# bcrypt only ever looks at the first 72 bytes, and bcrypt>=5 raises on
# anything longer — so this is a hard ceiling, not a preference.
MAX_PASSWORD_BYTES = 72
MAX_EMAIL_LENGTH = 254
# Deliberately loose (something@something.tld): the only real proof an
# address works is a delivered email; this just rejects obvious typos.
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

logger = logging.getLogger(__name__)


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidEmailError(ValueError):
    """Message is user-facing (French)."""


class InvalidPasswordError(ValueError):
    """Message is user-facing (French)."""


class WrongCurrentPasswordError(Exception):
    pass


def normalize_email(email: str) -> str:
    """Lowercased and trimmed, so Foo@x.com and foo@x.com are one account.
    Raises InvalidEmailError if it doesn't look like an email address."""
    normalized = email.strip().lower()
    if len(normalized) > MAX_EMAIL_LENGTH or not _EMAIL_PATTERN.match(normalized):
        raise InvalidEmailError("Adresse email invalide.")
    return normalized


def validate_new_password(password: str) -> None:
    """Policy for any password being set (signup, change, reset). Not
    applied at login, so accounts created before it can still sign in."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise InvalidPasswordError(
            f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères."
        )
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise InvalidPasswordError("Le mot de passe est trop long (72 caractères maximum).")


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _password_matches(user: User, password: str) -> bool:
    password_bytes = password.encode("utf-8")
    # Over the bcrypt limit can't match any stored hash (they were all
    # validated on the way in) — and bcrypt>=5 would raise on it.
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        return False
    return bcrypt.checkpw(password_bytes, user.password_hash.encode("utf-8"))


def find_user_by_email(db: Session, email: str) -> User | None:
    try:
        normalized = normalize_email(email)
    except InvalidEmailError:
        return None
    return db.execute(select(User).where(User.email == normalized)).scalar_one_or_none()


def register_user(db: Session, email: str, password: str, *, is_admin: bool = False) -> User:
    email = normalize_email(email)
    validate_new_password(password)
    user = User(email=email, password_hash=_hash_password(password), is_admin=is_admin)
    # A SAVEPOINT, not db.rollback(): rolling back the whole session would
    # also discard any other pending work a caller made in this same
    # transaction before calling register_user, not just this failed insert.
    try:
        with db.begin_nested():
            db.add(user)
            db.flush()
    except IntegrityError as exc:
        raise EmailAlreadyRegisteredError from exc
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = find_user_by_email(db, email)
    if user is None or not _password_matches(user, password):
        return None
    return user


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_session(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(32)
    session = UserSession(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(UTC) + SESSION_DURATION,
    )
    db.add(session)
    db.flush()
    return raw_token


def resolve_session(db: Session, raw_token: str) -> User | None:
    """Returns the user for a valid, unexpired session token, else None.

    Does not check is_admin — require_admin() does that on top of this.
    """
    session = db.execute(
        select(UserSession).where(UserSession.token_hash == _hash_token(raw_token))
    ).scalar_one_or_none()
    if session is None or session.expires_at < datetime.now(UTC):
        return None
    return db.get(User, session.user_id)


def delete_session(db: Session, raw_token: str) -> None:
    db.execute(delete(UserSession).where(UserSession.token_hash == _hash_token(raw_token)))


def revoke_sessions(db: Session, user: User, *, except_raw_token: str | None = None) -> None:
    """Logs the user out everywhere (optionally but the current session):
    after a password change, a session someone else had stolen must die."""
    statement = delete(UserSession).where(UserSession.user_id == user.id)
    if except_raw_token is not None:
        statement = statement.where(UserSession.token_hash != _hash_token(except_raw_token))
    db.execute(statement)


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    user = resolve_session(db, raw_token) if raw_token else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès réservé aux administrateurs")
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Like require_user(), but returns None instead of raising 401 — for
    routes usable both logged-out and logged-in (e.g. /suggestions), where a
    session only changes behaviour (applying preferences), never gates access.
    """
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    return resolve_session(db, raw_token) if raw_token else None


def create_reset_token(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(UTC) + RESET_TOKEN_DURATION,
    )
    db.add(reset_token)
    db.flush()
    return raw_token


def deliver_reset_link(user: User, raw_token: str) -> None:
    """Hands the reset link to the account owner — never to the HTTP caller,
    since whoever calls /password-reset/request is not necessarily the owner.

    No email-sending infra yet (see docs/ARCHITECTURE.md), so the link goes
    to the server log, which only the operator can read; they forward it to
    the user by hand. Logged at WARNING because uvicorn leaves the root
    logger unconfigured, and only WARNING+ reaches stderr through Python's
    last-resort handler. Swap this body for a real email send later.
    """
    link = f"{settings.frontend_base_url}/reset-password/confirm?token={raw_token}"
    logger.warning("Password reset link for %s (valid 1h, single use): %s", user.email, link)


def consume_reset_token(db: Session, raw_token: str, new_password: str) -> User | None:
    """Validates a reset token, applies the new password, and deletes the
    token so it can't be reused. Returns None (no-op) if the token is
    missing/expired. Raises InvalidPasswordError before touching the token,
    so a rejected password doesn't burn the link.

    Also revokes every session and every other reset token of the account:
    a reset is what someone does when they think it was compromised.
    """
    validate_new_password(new_password)
    token_hash = _hash_token(raw_token)
    reset_token = db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    ).scalar_one_or_none()
    if reset_token is None or reset_token.expires_at < datetime.now(UTC):
        return None
    user = db.get(User, reset_token.user_id)
    if user is None:
        return None
    user.password_hash = _hash_password(new_password)
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    revoke_sessions(db, user)
    db.flush()
    return user


def update_account(
    db: Session,
    user: User,
    *,
    current_password: str,
    email: str | None,
    password: str | None,
    current_raw_token: str | None = None,
) -> User:
    """Changing the email or password requires the current password, so a
    stolen session (or an unlocked laptop) can't take the account over. A
    password change logs out every other session (current_raw_token is the
    one kept)."""
    if not _password_matches(user, current_password):
        raise WrongCurrentPasswordError
    if email is not None:
        user.email = normalize_email(email)
    if password is not None:
        validate_new_password(password)
        user.password_hash = _hash_password(password)
        revoke_sessions(db, user, except_raw_token=current_raw_token)
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError as exc:
        raise EmailAlreadyRegisteredError from exc
    return user


def delete_account(db: Session, user: User) -> None:
    db.delete(user)
    db.flush()
