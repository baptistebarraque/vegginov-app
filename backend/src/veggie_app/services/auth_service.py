"""Authentication: password hashing, session issuing/validation, account
management.

resolve_session() is kept separate from require_user()/require_admin() so
session resolution can be tested directly with a DB session, without
needing to fabricate a FastAPI Request — require_user()/require_admin() are
the thin, FastAPI-specific wrappers routes actually depend on.
"""

import hashlib
import logging
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

logger = logging.getLogger(__name__)


class EmailAlreadyRegisteredError(Exception):
    pass


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def register_user(db: Session, email: str, password: str, *, is_admin: bool = False) -> User:
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
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not bcrypt.checkpw(
        password.encode("utf-8"), user.password_hash.encode("utf-8")
    ):
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
    missing/expired.
    """
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
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    db.flush()
    return user


def update_account(
    db: Session, user: User, *, email: str | None, password: str | None
) -> User:
    if email is not None:
        user.email = email
    if password is not None:
        user.password_hash = _hash_password(password)
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError as exc:
        raise EmailAlreadyRegisteredError from exc
    return user


def delete_account(db: Session, user: User) -> None:
    db.delete(user)
    db.flush()
