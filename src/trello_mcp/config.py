"""Конфигурация сервера: загрузка env через pydantic-settings.

Обязательные переменные (TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_BOARD_ID) не имеют
значений по умолчанию — при их отсутствии инициализация Settings падает с явной
ошибкой валидации. Логирование настраивается на stderr, потому что stdout в
stdio-режиме занят JSON-RPC.
"""

from __future__ import annotations

import logging
import sys

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки сервера, читаемые из окружения или файла .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    trello_api_key: str = Field(description="Trello API key.")
    trello_token: str = Field(description="Trello API token.")
    trello_board_id: str = Field(description="Идентификатор доски, которой управляет сервер.")

    trello_api_base: str = Field(
        default="https://api.trello.com/1",
        description="Базовый URL Trello REST API.",
    )
    log_level: str = Field(default="INFO", description="Уровень логирования (DEBUG/INFO/...).")


def get_settings() -> Settings:
    """Прочитать настройки из env. Бросает ValidationError без обязательных переменных."""
    return Settings()


def configure_logging(level: str = "INFO") -> None:
    """Настроить логирование строго в stderr (stdout занят JSON-RPC в stdio-режиме)."""
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
