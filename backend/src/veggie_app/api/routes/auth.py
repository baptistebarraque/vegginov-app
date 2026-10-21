"""POST /auth/login, /auth/signup, /auth/logout, GET /auth/me,
password-reset request/confirm, account update/delete.

Session-cookie mechanics (set_cookie/delete_cookie) live here since they're
an HTTP concern, not business logic.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
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
from veggie_app.services import auth_service, rate_limit_service
from veggie_app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidEmailError,
    InvalidPasswordError,
    WrongCurrentPasswordError,
)
from veggie_app.services.rate_limit_service import (
    ACCOUNT_UPDATE_LIMITER,
    LOGIN_LIMITER,
    PASSWORD_RESET_LIMITER,
    SIGNUP_LIMITER,
)

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


@router.post(
    "/signup",
    response_model=UserResponse,
    dependencies=[Depends(rate_limit_service.limit(SIGNUP_LIMITER))],
)
def signup(
    request: SignupRequest, response: Response, db: Session = Depends(get_db)
) -> UserResponse:
    try:
        user = auth_service.register_user(db, request.email, request.password, is_admin=False)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cet email est déjà utilisé") from exc
    except (InvalidEmailError, InvalidPasswordError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    token = auth_service.create_session(db, user)
    db.commit()
    _set_session_cookie(response, token)
    return UserResponse(email=user.email, is_admin=user.is_admin)


@router.post(
    "/login",
    response_model=UserResponse,
    dependencies=[Depends(rate_limit_service.limit(LOGIN_LIMITER))],
)
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


@router.post(
    "/password-reset/request",
    response_model=StatusResponse,
    dependencies=[Depends(rate_limit_service.limit(PASSWORD_RESET_LIMITER))],
)
def request_password_reset(
    request: RequestPasswordResetRequest, db: Session = Depends(get_db)
) -> StatusResponse:
    # Same response whether or not the email exists, so this endpoint can't
    # be used to enumerate registered accounts — and the token itself is
    # never in the response, only delivered out of band to the owner.
    user = auth_service.find_user_by_email(db, request.email)
    if user is not None:
        token = auth_service.create_reset_token(db, user)
        db.commit()
        auth_service.deliver_reset_link(user, token)
    return StatusResponse(status="ok")


@router.post("/password-reset/confirm", response_model=StatusResponse)
def confirm_password_reset(
    request: ConfirmPasswordResetRequest, db: Session = Depends(get_db)
) -> StatusResponse:
    try:
        user = auth_service.consume_reset_token(db, request.token, request.new_password)
    except InvalidPasswordError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    if user is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Lien de réinitialisation invalide ou expiré"
        )
    db.commit()
    return StatusResponse(status="ok")


@router.patch(
    "/account",
    response_model=UserResponse,
    dependencies=[Depends(rate_limit_service.limit(ACCOUNT_UPDATE_LIMITER))],
)
def update_account(
    request: UpdateAccountRequest,
    http_request: Request,
    user: User = Depends(auth_service.require_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    try:
        user = auth_service.update_account(
            db,
            user,
            current_password=request.current_password,
            email=request.email,
            password=request.password,
            current_raw_token=http_request.cookies.get(auth_service.SESSION_COOKIE_NAME),
        )
    except WrongCurrentPasswordError as exc:
        # 400, not 401: the session is fine, only the confirmation failed —
        # a 401 would make the frontend treat the user as logged out.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mot de passe actuel incorrect.") from exc
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cet email est déjà utilisé") from exc
    except (InvalidEmailError, InvalidPasswordError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
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
