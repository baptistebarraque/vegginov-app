"""POST /auth/login, /auth/logout, GET /auth/me.

Validate input, call the service, serialize output. Session-cookie
mechanics (set_cookie/delete_cookie) live here since they're an HTTP
concern, not business logic.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from veggie_app.database import get_db
from veggie_app.models.user import User
from veggie_app.schemas.auth import LoginRequest, StatusResponse, UserResponse
from veggie_app.services import auth_service

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=UserResponse)
def login(
    request: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> UserResponse:
    user = auth_service.authenticate(db, request.email, request.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants invalides")

    token = auth_service.create_session(db, user)
    db.commit()

    response.set_cookie(
        auth_service.SESSION_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=False,  # local dev over http://localhost; must be True behind HTTPS
        max_age=int(auth_service.SESSION_DURATION.total_seconds()),
    )
    return UserResponse(email=user.email)


@router.post("/logout", response_model=StatusResponse)
def logout(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> StatusResponse:
    raw_token = request.cookies.get(auth_service.SESSION_COOKIE_NAME)
    if raw_token is not None:
        auth_service.delete_session(db, raw_token)
        db.commit()
    response.delete_cookie(auth_service.SESSION_COOKIE_NAME)
    return StatusResponse(status="ok")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(auth_service.require_admin)) -> UserResponse:
    return UserResponse(email=user.email)
