"""Request/response models for the auth API. Validation only, no logic."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    email: str
    is_admin: bool


class StatusResponse(BaseModel):
    status: str


class RequestPasswordResetRequest(BaseModel):
    email: str


class RequestPasswordResetResponse(BaseModel):
    status: str
    # Present only because there is no email-sending infra yet (see
    # docs/ARCHITECTURE.md) — the raw reset token/link is handed back here
    # instead of being emailed. Must be removed once real delivery exists.
    reset_token: str | None = None


class ConfirmPasswordResetRequest(BaseModel):
    token: str
    new_password: str


class UpdateAccountRequest(BaseModel):
    email: str | None = None
    password: str | None = None
