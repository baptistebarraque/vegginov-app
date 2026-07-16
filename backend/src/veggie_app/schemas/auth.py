"""Request/response models for the auth API. Validation only, no logic."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    email: str


class StatusResponse(BaseModel):
    status: str
