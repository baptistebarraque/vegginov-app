import pytest
from pydantic import ValidationError

from veggie_app.config import Settings

DEV_DATABASE_URL = "postgresql+psycopg://veggie:veggie@localhost:5432/veggie_app"
STRONG_DATABASE_URL = "postgresql+psycopg://veggie:Xq3v9LmT2rWk8sPz4bNc@postgres:5432/veggie_app"
PRODUCTION_SETTINGS = {
    "app_env": "production",
    "database_url": STRONG_DATABASE_URL,
    "cors_allowed_origins": "https://vegginov.example",
    "frontend_base_url": "https://vegginov.example",
}


def _settings(**overrides: object) -> Settings:
    # _env_file=None: only what the test passes, not the developer's .env.
    return Settings(_env_file=None, **overrides)


def test_defaults_are_development_with_insecure_cookie() -> None:
    settings = _settings(database_url=DEV_DATABASE_URL)

    assert settings.app_env == "development"
    assert settings.cookie_secure is False
    assert settings.cors_allowed_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_cors_allowed_origins_is_parsed_from_a_comma_separated_string() -> None:
    settings = _settings(
        database_url=DEV_DATABASE_URL,
        cors_allowed_origins=" https://a.example , https://b.example,",
    )

    assert settings.cors_allowed_origins == ["https://a.example", "https://b.example"]


def test_production_with_safe_settings_starts_with_secure_cookie() -> None:
    settings = _settings(**PRODUCTION_SETTINGS)

    assert settings.cookie_secure is True
    assert settings.cors_allowed_origins == ["https://vegginov.example"]


@pytest.mark.parametrize(
    ("override", "expected_message"),
    [
        ({"database_url": DEV_DATABASE_URL}, "database password"),
        (
            {"database_url": "postgresql+psycopg://veggie:short@postgres:5432/veggie_app"},
            "database password",
        ),
        ({"cors_allowed_origins": "http://vegginov.example"}, "CORS_ALLOWED_ORIGINS"),
        ({"cors_allowed_origins": ""}, "CORS_ALLOWED_ORIGINS is empty"),
        ({"frontend_base_url": "http://vegginov.example"}, "FRONTEND_BASE_URL"),
    ],
)
def test_production_refuses_dev_only_settings(
    override: dict[str, str], expected_message: str
) -> None:
    with pytest.raises(ValidationError, match=expected_message):
        _settings(**{**PRODUCTION_SETTINGS, **override})


def test_development_tolerates_the_dev_defaults() -> None:
    # The guard is production-only: local runs and CI keep veggie/veggie.
    settings = _settings(database_url=DEV_DATABASE_URL, cors_allowed_origins="http://x")

    assert settings.cors_allowed_origins == ["http://x"]
