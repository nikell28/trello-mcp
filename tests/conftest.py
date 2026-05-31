"""Общие фикстуры тестов.

Фикстуры дают тестовый конфиг с фейковыми кредами (через monkeypatch env) и
подготовленный respx-роутер. В Спринте 0 respx-мок не наполняется маршрутами —
он лишь закрепляет инфраструктуру для TDD в Спринте 1.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
import respx

from trello_mcp.config import Settings

_FAKE_ENV = {
    "TRELLO_API_KEY": "test-key",
    "TRELLO_TOKEN": "test-token",
    "TRELLO_BOARD_ID": "test-board",
    "TRELLO_API_BASE": "https://api.trello.com/1",
    "LOG_LEVEL": "INFO",
}


@pytest.fixture
def fake_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Проставить фейковые обязательные env-переменные Trello в окружение."""
    for key, value in _FAKE_ENV.items():
        monkeypatch.setenv(key, value)
    return dict(_FAKE_ENV)


@pytest.fixture
def settings(fake_env: dict[str, str]) -> Settings:
    """Готовый объект Settings на фейковых кредах."""
    return Settings()


@pytest.fixture
def respx_mock() -> Iterator[respx.MockRouter]:
    """Подготовленный respx-роутер (в Спринте 0 маршруты не задаются)."""
    with respx.mock(base_url="https://api.trello.com/1", assert_all_called=False) as router:
        yield router
