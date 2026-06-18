"""Тесты инструмента get_boards.

TC-TMCP-08-1..4 — инструмент get_boards (US-TMCP-08).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from trello_mcp.config import Settings
from trello_mcp.errors import TrelloAuthError
from trello_mcp.trello_client import TrelloClient


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[TrelloClient]:
    async with TrelloClient(settings) as c:
        yield c


async def test_tc_tmcp_08_1_returns_all_boards(
    client: TrelloClient, respx_mock: respx.MockRouter
) -> None:
    """TC-TMCP-08-1 — Возврат всех открытых досок пользователя."""
    # Given: замокан GET /members/me/boards, возвращает 3 доски
    respx_mock.get("/members/me/boards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "b1", "name": "Project A"},
                {"id": "b2", "name": "Project B"},
                {"id": "b3", "name": "Personal"},
            ],
        )
    )
    # When: вызывается инструмент get_boards
    boards = await client.get_boards()
    # Then: возвращаются 3 доски, каждая содержит id и name
    assert len(boards) == 3
    assert all(board.id and board.name for board in boards)


async def test_tc_tmcp_08_2_correct_url_and_auth(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-TMCP-08-2 — Корректный URL и авторизация в запросе."""
    # Given: замокан Trello API, креды из конфига
    route = respx_mock.get("/members/me/boards").mock(
        return_value=httpx.Response(200, json=[])
    )
    async with TrelloClient(settings) as client:
        # When: вызывается get_boards
        await client.get_boards()
    # Then: запрос уходит на /members/me/boards с key и token в query
    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["key"] == "test-key"
    assert params["token"] == "test-token"


async def test_tc_tmcp_08_3_filter_open_in_request(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-TMCP-08-3 — Заархивированные доски исключены (filter=open)."""
    # Given: замокан API
    route = respx_mock.get("/members/me/boards").mock(
        return_value=httpx.Response(200, json=[])
    )
    async with TrelloClient(settings) as client:
        # When: вызывается get_boards
        await client.get_boards()
    # Then: в запросе присутствует filter=open
    params = dict(route.calls.last.request.url.params)
    assert params["filter"] == "open"


async def test_tc_tmcp_08_4_401_raises_auth_error(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-TMCP-08-4 — Ошибка 401 возвращается читаемым текстом (TrelloAuthError)."""
    # Given: замокан API, возвращает 401
    respx_mock.get("/members/me/boards").mock(
        return_value=httpx.Response(
            401,
            json={"error": "Unauthorized"},
        )
    )
    async with TrelloClient(settings) as client:
        # When: вызывается get_boards
        # Then: выбрасывается TrelloAuthError
        with pytest.raises(TrelloAuthError):
            await client.get_boards()
