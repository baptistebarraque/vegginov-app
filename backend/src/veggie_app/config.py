"""Typed application settings, loaded from environment variables / .env."""

from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import make_url

# Shipped in .env.example and CI — fine on a dev machine, never on a server.
DEFAULT_DB_PASSWORD = "veggie"
MIN_PRODUCTION_DB_PASSWORD_LENGTH = 16


class Settings(BaseSettings):
    # Repo root .env, since backend commands are run with `cd backend` first
    # (see CLAUDE.md "Commands"). Inside Docker this file won't exist at all,
    # which is fine: docker-compose's `env_file` already injects real env
    # vars, and a missing env_file is silently ignored by pydantic-settings.
    # hide_input_in_errors: a validation error must not echo DATABASE_URL
    # (and its password) into the startup logs.
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore", hide_input_in_errors=True)

    database_url: str
    # Relative to cwd: `backend/uploads` when run locally (`cd backend` first,
    # per CLAUDE.md), `/app/uploads` in Docker (WORKDIR is /app). Same
    # relative path in both cases keeps the CLI and web upload path writing
    # to the same place — see docker-compose.yml's bind mount for this dir.
    upload_dir: Path = Path("uploads")
    # Same reasoning as upload_dir: bind-mounted rather than baked into the
    # Docker image, since these are large external files not committed to
    # git — see backend/data/flavorgraph/README.md.
    flavorgraph_dir: Path = Path("data/flavorgraph")
    # Origin the password-reset link points at (the frontend, not this API).
    # Defaults to the Vite dev server; set to the public URL once deployed.
    frontend_base_url: str = "http://localhost:5173"
    # The one switch between local dev and a real deployment. "production"
    # marks the session cookie Secure (sent over HTTPS only) and refuses to
    # start on settings that are only acceptable on a dev machine — see
    # _check_production_safety. Defaults to development so local runs, tests
    # and CI need no extra configuration.
    app_env: Literal["development", "production"] = "development"
    # Browser origins allowed to call the API with the session cookie.
    # Comma-separated in the env var (NoDecode: pydantic-settings would
    # otherwise expect a JSON list). Both localhost forms by default, since
    # browsers treat localhost and 127.0.0.1 as different origins.
    cors_allowed_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _check_production_safety(self) -> Self:
        if self.app_env != "production":
            return self
        problems = []
        db_password = make_url(self.database_url).password or ""
        if (
            db_password == DEFAULT_DB_PASSWORD
            or len(db_password) < MIN_PRODUCTION_DB_PASSWORD_LENGTH
        ):
            problems.append(
                "the database password is the dev default or shorter than "
                f"{MIN_PRODUCTION_DB_PASSWORD_LENGTH} characters"
            )
        if not self.cors_allowed_origins:
            problems.append("CORS_ALLOWED_ORIGINS is empty")
        insecure_origins = [o for o in self.cors_allowed_origins if not o.startswith("https://")]
        if insecure_origins:
            problems.append(f"CORS_ALLOWED_ORIGINS must all be https:// ({insecure_origins})")
        if not self.frontend_base_url.startswith("https://"):
            problems.append("FRONTEND_BASE_URL must be https://")
        if problems:
            raise ValueError("Unsafe production settings: " + "; ".join(problems))
        return self

    @property
    def cookie_secure(self) -> bool:
        return self.app_env == "production"


settings = Settings()
