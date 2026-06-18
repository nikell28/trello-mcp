"""Тесты multi-board поддержки: _resolve_board_id и инструменты сервера.

Unit-тесты для _resolve_board_id:
- явный board_id → возвращает его
- board_id=None, settings.trello_board_id задан → возвращает из конфига
- board_id=None, settings.trello_board_id=None → ValueError с читаемым текстом

Integration-тесты для инструментов (мок TrelloClient):
- get_lists(board_id="X") вызывает client.get_lists(board_id="X")
- get_lists() с TRELLO_BOARD_ID=default → вызывает client.get_lists(board_id="default")
- get_lists() без board_id и без TRELLO_BOARD_ID → возвращает строку с ошибкой
(аналогично для get_cards и get_labels)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from trello_mcp.config import Settings
from trello_mcp.models import Label, List
from trello_mcp.server import _resolve_board_id

# ---------------------------------------------------------------------------
# Unit-тесты _resolve_board_id
# ---------------------------------------------------------------------------


def _make_settings(board_id: str | None) -> Settings:
    """Создать Settings с заданным trello_board_id, минуя .env."""
    return Settings(
        trello_api_key="key",
        trello_token="token",
        trello_board_id=board_id,
        _env_file=None,  # type: ignore[call-arg]
    )


def test_resolve_board_id_explicit_wins() -> None:
    """Явный board_id возвращается как есть, независимо от конфига."""
    settings = _make_settings("config-board")
    result = _resolve_board_id("explicit-board", settings)
    assert result == "explicit-board"


def test_resolve_board_id_fallback_to_config() -> None:
    """board_id=None → используется значение из settings.trello_board_id."""
    settings = _make_settings("default-board")
    result = _resolve_board_id(None, settings)
    assert result == "default-board"


def test_resolve_board_id_no_board_raises_value_error() -> None:
    """board_id=None и settings.trello_board_id=None → ValueError с читаемым текстом."""
    settings = _make_settings(None)
    with pytest.raises(ValueError) as exc_info:
        _resolve_board_id(None, settings)
    error_text = str(exc_info.value)
    assert "board_id" in error_text
    assert "TRELLO_BOARD_ID" in error_text


# ---------------------------------------------------------------------------
# Integration-тесты инструментов сервера
# ---------------------------------------------------------------------------

_FAKE_LIST = List(id="l1", name="To Do", closed=False, pos=1.0)
_FAKE_LABEL = Label(id="lb1", name="Bug", color="red")


@pytest.fixture
def settings_with_board() -> Settings:
    return _make_settings("default-board")


@pytest.fixture
def settings_no_board() -> Settings:
    return _make_settings(None)


async def test_get_lists_explicit_board_id_passed_to_client(
    settings_with_board: Settings,
) -> None:
    """get_lists(board_id="X") вызывает client.get_lists(board_id="X")."""
    from trello_mcp import server

    mock_client = AsyncMock()
    mock_client.get_lists = AsyncMock(return_value=[_FAKE_LIST])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch.object(server, "get_settings", return_value=settings_with_board),
        patch("trello_mcp.server.TrelloClient", return_value=mock_client),
    ):
        result = await server.get_lists(board_id="explicit-board")

    mock_client.get_lists.assert_called_once_with(board_id="explicit-board")
    assert isinstance(result, list)


async def test_get_lists_fallback_to_config_board(settings_with_board: Settings) -> None:
    """get_lists() без board_id → передаёт settings.trello_board_id в клиент."""
    from trello_mcp import server

    mock_client = AsyncMock()
    mock_client.get_lists = AsyncMock(return_value=[_FAKE_LIST])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch.object(server, "get_settings", return_value=settings_with_board),
        patch("trello_mcp.server.TrelloClient", return_value=mock_client),
    ):
        result = await server.get_lists(board_id=None)

    mock_client.get_lists.assert_called_once_with(board_id="default-board")
    assert isinstance(result, list)


async def test_get_lists_no_board_returns_error_string(settings_no_board: Settings) -> None:
    """get_lists() без board_id и без TRELLO_BOARD_ID → строка с ошибкой."""
    from trello_mcp import server

    mock_client = MagicMock()

    with (
        patch.object(server, "get_settings", return_value=settings_no_board),
        patch("trello_mcp.server.TrelloClient", return_value=mock_client),
    ):
        result = await server.get_lists(board_id=None)

    assert isinstance(result, str)
    assert "board_id" in result or "TRELLO_BOARD_ID" in result


async def test_get_cards_explicit_board_id_passed_to_client(
    settings_with_board: Settings,
) -> None:
    """get_cards(board_id="X") вызывает client.get_cards(board_id="X")."""
    from trello_mcp import server
    from trello_mcp.models import CardBrief

    fake_card = CardBrief.model_validate({"id": "c1", "name": "Card", "idList": "l1", "labels": []})
    mock_client = AsyncMock()
    mock_client.get_cards = AsyncMock(return_value=[fake_card])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch.object(server, "get_settings", return_value=settings_with_board),
        patch("trello_mcp.server.TrelloClient", return_value=mock_client),
    ):
        result = await server.get_cards(board_id="explicit-board")

    mock_client.get_cards.assert_called_once_with(board_id="explicit-board")
    assert isinstance(result, list)


async def test_get_cards_no_board_returns_error_string(settings_no_board: Settings) -> None:
    """get_cards() без board_id и без TRELLO_BOARD_ID → строка с ошибкой."""
    from trello_mcp import server

    mock_client = MagicMock()

    with (
        patch.object(server, "get_settings", return_value=settings_no_board),
        patch("trello_mcp.server.TrelloClient", return_value=mock_client),
    ):
        result = await server.get_cards(board_id=None)

    assert isinstance(result, str)
    assert "board_id" in result or "TRELLO_BOARD_ID" in result


async def test_get_labels_explicit_board_id_passed_to_client(
    settings_with_board: Settings,
) -> None:
    """get_labels(board_id="X") вызывает client.get_labels(board_id="X")."""
    from trello_mcp import server

    mock_client = AsyncMock()
    mock_client.get_labels = AsyncMock(return_value=[_FAKE_LABEL])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch.object(server, "get_settings", return_value=settings_with_board),
        patch("trello_mcp.server.TrelloClient", return_value=mock_client),
    ):
        result = await server.get_labels(board_id="explicit-board")

    mock_client.get_labels.assert_called_once_with(board_id="explicit-board")
    assert isinstance(result, list)


async def test_get_labels_fallback_to_config_board(settings_with_board: Settings) -> None:
    """get_labels() без board_id → передаёт settings.trello_board_id в клиент."""
    from trello_mcp import server

    mock_client = AsyncMock()
    mock_client.get_labels = AsyncMock(return_value=[_FAKE_LABEL])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch.object(server, "get_settings", return_value=settings_with_board),
        patch("trello_mcp.server.TrelloClient", return_value=mock_client),
    ):
        result = await server.get_labels(board_id=None)

    mock_client.get_labels.assert_called_once_with(board_id="default-board")
    assert isinstance(result, list)


async def test_get_labels_no_board_returns_error_string(settings_no_board: Settings) -> None:
    """get_labels() без board_id и без TRELLO_BOARD_ID → строка с ошибкой."""
    from trello_mcp import server

    mock_client = MagicMock()

    with (
        patch.object(server, "get_settings", return_value=settings_no_board),
        patch("trello_mcp.server.TrelloClient", return_value=mock_client),
    ):
        result = await server.get_labels(board_id=None)

    assert isinstance(result, str)
    assert "board_id" in result or "TRELLO_BOARD_ID" in result
