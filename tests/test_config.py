"""Тесты конфигурации: читается при наличии env, падает без обязательных переменных."""

from __future__ import annotations

import logging
import sys

import pytest
from pydantic import ValidationError

from trello_mcp.config import Settings, configure_logging, get_settings


def test_settings_loaded_from_env(fake_env: dict[str, str]) -> None:
    settings = get_settings()
    assert settings.trello_api_key == fake_env["TRELLO_API_KEY"]
    assert settings.trello_token == fake_env["TRELLO_TOKEN"]
    assert settings.trello_board_id == fake_env["TRELLO_BOARD_ID"]


def test_settings_defaults(fake_env: dict[str, str]) -> None:
    settings = get_settings()
    assert settings.trello_api_base == "https://api.trello.com/1"
    assert settings.log_level == "INFO"


def test_settings_missing_required_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("TRELLO_API_KEY", "TRELLO_TOKEN", "TRELLO_BOARD_ID"):
        monkeypatch.delenv(key, raising=False)
    # Запрет чтения настоящего .env, чтобы тест не зависел от локального файла.
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_configure_logging_writes_to_stderr() -> None:
    configure_logging("DEBUG")
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert len(root.handlers) == 1
    handler = root.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    # Логи идут в stderr, не в stdout (stdout занят JSON-RPC в stdio-режиме).
    assert handler.stream is sys.stderr
    assert handler.stream is not sys.stdout
