"""POST /auth/login, /auth/signup, /auth/logout, GET /auth/me,
password-reset request/confirm, account update/delete.

Session-cookie mechanics (set_cookie/delete_cookie) live here since they're
an HTTP concern, not business logic.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from veggie_app.config import settings
from veggie_app.database import get_db
from veggie_app.models.user import User
from veggie_app.schemas.auth import (
    ConfirmPasswordResetRequest,
    LoginRequest,
    RequestPasswordResetRequest,
    SignupRequest,
    StatusResponse,
    UpdateAccountRequest,
    UserResponse,
)
from veggie_app.services import auth_service
from veggie_app.services.auth_service import EmailAlreadyRegisteredError

router = APIRouter(prefix="/auth")


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        auth_service.SESSION_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        # Secure in production (HTTPS only); off in dev, where the API is
        # plain http://localhost — see APP_ENV in config.py.
        secure=settings.cookie_secure,
        max_age=int(auth_service.SESSION_DURATION.total_seconds()),
    )


def _clear_session_cookie(response: Response) -> None:
    # Same attributes as _set_session_cookie, so the deleting Set-Cookie
    # matches the cookie it replaces.
    response.delete_cookie(
        auth_service.SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )


@router.post("/signup", response_model=UserResponse)
def signup(
    request: SignupRequest, response: Response, db: Session = Depends(get_db)
) -> UserResponse:
    try:
        user = auth_service.register_user(db, request.email, request.password, is_admin=False)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cet email est déjà utilisé") from exc

    token = auth_service.create_session(db, user)
    db.commit()
    _set_session_cookie(response, token)
    return UserResponse(email=user.email, is_admin=user.is_admin)


@router.post("/login", response_model=UserResponse)
def login(
    request: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> UserResponse:
    user = auth_service.authenticate(db, request.email, request.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants invalides")

    token = auth_service.create_session(db, user)
    db.commit()
    _set_session_cookie(response, token)
    return UserResponse(email=user.email, is_admin=user.is_admin)


@router.post("/logout", response_model=StatusResponse)
def logout(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> StatusResponse:
    raw_token = request.cookies.get(auth_service.SESSION_COOKIE_NAME)
    if raw_token is not None:
        auth_service.delete_session(db, raw_token)
        db.commit()
    _clear_session_cookie(response)
    return StatusResponse(status="ok")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(auth_service.require_user)) -> UserResponse:
    return UserResponse(email=user.email, is_admin=user.is_admin)


@router.post("/password-reset/request", response_model=StatusResponse)
def request_password_reset(
    request: RequestPasswordResetRequest, db: Session = Depends(get_db)
) -> StatusResponse:
    # Same response whether or not the email exists, so this endpoint can't
    # be used to enumerate registered accounts — and the token itself is
    # never in the response, only delivered out of band to the owner.
    user = db.execute(select(User).where(User.email == request.email)).scalar_one_or_none()
    if user is not None:
        token = auth_service.create_reset_token(db, user)
        db.commit()
        auth_service.deliver_reset_link(user, token)
    return StatusResponse(status="ok")


@router.post("/password-reset/confirm", response_model=StatusResponse)
def confirm_password_reset(
    request: ConfirmPasswordResetRequest, db: Session = Depends(get_db)
) -> StatusResponse:
    user = auth_service.consume_reset_token(db, request.token, request.new_password)
    if user is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Lien de réinitialisation invalide ou expiré"
        )
    db.commit()
    return StatusResponse(status="ok")


@router.patch("/account", response_model=UserResponse)
def update_account(
    request: UpdateAccountRequest,
    user: User = Depends(auth_service.require_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    try:
        user = auth_service.update_account(
            db, user, email=request.email, password=request.password
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cet email est déjà utilisé") from exc
    db.commit()
    return UserResponse(email=user.email, is_admin=user.is_admin)


@router.delete("/account", response_model=StatusResponse)
def delete_account(
    response: Response,
    user: User = Depends(auth_service.require_user),
    db: Session = Depends(get_db),
) -> StatusResponse:
    auth_service.delete_account(db, user)
    db.commit()
    _clear_session_cookie(response)
    return StatusResponse(status="ok")
