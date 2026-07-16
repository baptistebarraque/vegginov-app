"""Admin authentication: password hashing, session issuing/validation.

resolve_session() is kept separate from require_admin() so session
resolution can be tested directly with a DB session, without needing to
fabricate a FastAPI Request — require_admin() is the thin, FastAPI-specific
wrapper that routes actually depend on.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from veggie_app.database import get_db
from veggie_app.models.admin_session import AdminSession
from veggie_app.models.user import User

SESSION_COOKIE_NAME = "session_token"
SESSION_DURATION = timedelta(days=7)


def create_admin(db: Session, email: str, password: str) -> User:
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(email=email, password_hash=password_hash, is_admin=True)
    db.add(user)
    db.flush()
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
    session = AdminSession(
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
        select(AdminSession).where(AdminSession.token_hash == _hash_token(raw_token))
    ).scalar_one_or_none()
    if session is None or session.expires_at < datetime.now(UTC):
        return None
    return db.get(User, session.user_id)


def delete_session(db: Session, raw_token: str) -> None:
    db.execute(delete(AdminSession).where(AdminSession.token_hash == _hash_token(raw_token)))


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    user = resolve_session(db, raw_token) if raw_token else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise")
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès réservé aux administrateurs")
    return user
