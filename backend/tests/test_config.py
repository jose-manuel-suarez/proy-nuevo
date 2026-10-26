from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_accept_explicit_values() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@db:5432/app",
        service_token="token",
    )

    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.app_env == "development"


def test_empty_database_url_is_rejected() -> None:
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, database_url="", service_token="token")

    assert "database_url" in str(error.value)


def test_empty_service_token_is_rejected() -> None:
    with pytest.raises(ValidationError) as error:
        Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://user:pass@db:5432/app",
            service_token="",
        )

    assert "service_token" in str(error.value)


def test_missing_environment_values_fail_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SERVICE_TOKEN", raising=False)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    message = str(error.value)
    assert "database_url" in message
    assert "service_token" in message
