"""Request/response models for the auth API. Validation only, no logic."""

from pydantic import BaseModel, Field

# Generous ceilings that only bound the payload size; the real email and
# password rules (with French messages) live in auth_service.
_EMAIL_FIELD = Field(max_length=320)
_PASSWORD_FIELD = Field(max_length=256)


class LoginRequest(BaseModel):
    email: str = _EMAIL_FIELD
    password: str = _PASSWORD_FIELD


class SignupRequest(BaseModel):
    email: str = _EMAIL_FIELD
    password: str = _PASSWORD_FIELD


class UserResponse(BaseModel):
    email: str
    is_admin: bool


class StatusResponse(BaseModel):
    status: str


class RequestPasswordResetRequest(BaseModel):
    email: str = _EMAIL_FIELD


class ConfirmPasswordResetRequest(BaseModel):
    token: str = Field(max_length=256)
    new_password: str = _PASSWORD_FIELD


class UpdateAccountRequest(BaseModel):
    current_password: str = _PASSWORD_FIELD
    email: str | None = Field(default=None, max_length=320)
    password: str | None = Field(default=None, max_length=256)
