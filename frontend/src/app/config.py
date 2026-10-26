"""Frontend configuration, read from the environment with required values."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    log_level: str = "INFO"

    secret_key: str = Field(min_length=1)
    service_token: str = Field(min_length=1)
    backend_url: str = Field(min_length=1)
    request_timeout: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
