"""Настройки API-сервиса (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # База данных
    database_url: str = "postgresql+psycopg2://app:change_me@localhost:5432/price_tracker"

    # Celery / Redis (нужны API, чтобы ставить задачи в очередь)
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Внутренняя аутентификация между ботом и API
    internal_api_token: str = "dev-internal-token"

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
