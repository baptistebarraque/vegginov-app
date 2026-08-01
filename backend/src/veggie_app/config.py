"""Typed application settings, loaded from environment variables / .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Repo root .env, since backend commands are run with `cd backend` first
    # (see CLAUDE.md "Commands"). Inside Docker this file won't exist at all,
    # which is fine: docker-compose's `env_file` already injects real env
    # vars, and a missing env_file is silently ignored by pydantic-settings.
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

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


settings = Settings()
