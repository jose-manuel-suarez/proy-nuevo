"""Application settings.

Every value that changes between environments is read from the environment.
Required values have no defaults: a missing configuration fails loudly at
startup instead of falling back to a usable-looking secret.
"""

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

    database_url: str = Field(min_length=1)
    service_token: str = Field(min_length=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
