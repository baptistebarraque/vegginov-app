"""Typed application settings, loaded from environment variables / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Repo root .env, since backend commands are run with `cd backend` first
    # (see CLAUDE.md "Commands"). Inside Docker this file won't exist at all,
    # which is fine: docker-compose's `env_file` already injects real env
    # vars, and a missing env_file is silently ignored by pydantic-settings.
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str


settings = Settings()
