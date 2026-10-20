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


class ConfirmPasswordResetRequest(BaseModel):
    token: str
    new_password: str


class UpdateAccountRequest(BaseModel):
    email: str | None = None
    password: str | None = None
