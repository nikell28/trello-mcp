"""Тесты инструмента get_boards на уровне сервера (FastMCP).

TC-TMCP-09-1..3 — инструмент get_boards с фильтром (US-TMCP-09).
TC-TMCP-10-1   — инструмент get_boards без фильтра (US-TMCP-10).
"""

from __future__ import annotations

import httpx
import respx

from trello_mcp.config import Settings
from trello_mcp.server import get_boards


async def test_tc_tmcp_09_1_returns_all_boards_without_filter(
    settings: Settings,
    respx_mock: respx.MockRouter,
) -> None:
    """TC-TMCP-09-1 — Инструмент возвращает все доски без фильтра."""
    # Given: замокан API, возвращает 3 доски
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
    # When: вызывается инструмент без фильтра
    result = await get_boards(name=None)
    # Then: возвращаются все 3 доски
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0]["name"] == "Project A"
    assert result[1]["name"] == "Project B"
    assert result[2]["name"] == "Personal"


async def test_tc_tmcp_09_2_filters_by_exact_name_case_insensitive(
    settings: Settings,
    respx_mock: respx.MockRouter,
) -> None:
    """TC-TMCP-09-2 — Инструмент фильтрует по названию (регистронезависимое точное совпадение)."""
    # Given: замокан API, возвращает 3 доски
    respx_mock.get("/members/me/boards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "b1", "name": "Project A"},
                {"id": "b2", "name": "project a"},
                {"id": "b3", "name": "Personal"},
            ],
        )
    )
    # When: вызывается инструмент с фильтром "project a"
    result = await get_boards(name="project a")
    # Then: возвращаются только доски с точным совпадением (регистронезависимое)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(board["name"].lower() == "project a" for board in result)


async def test_tc_tmcp_09_3_returns_empty_list_when_no_match(
    settings: Settings,
    respx_mock: respx.MockRouter,
) -> None:
    """TC-TMCP-09-3 — Инструмент возвращает пустой список если нет совпадений."""
    # Given: замокан API, возвращает 2 доски
    respx_mock.get("/members/me/boards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "b1", "name": "Project A"},
                {"id": "b2", "name": "Project B"},
            ],
        )
    )
    # When: вызывается инструмент с фильтром "NonExistent"
    result = await get_boards(name="NonExistent")
    # Then: возвращается пустой список
    assert isinstance(result, list)
    assert len(result) == 0


async def test_tc_tmcp_10_1_returns_board_dict_with_id_and_name(
    settings: Settings,
    respx_mock: respx.MockRouter,
) -> None:
    """TC-TMCP-10-1 — Инструмент возвращает доски с полями id и name."""
    # Given: замокан API
    respx_mock.get("/members/me/boards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "b1", "name": "Project A", "closed": False, "url": "https://..."},
                {"id": "b2", "name": "Project B", "closed": False},
            ],
        )
    )
    # When: вызывается инструмент
    result = await get_boards()
    # Then: каждая доска содержит только id и name (остальные поля отфильтрованы)
    assert isinstance(result, list)
    assert len(result) == 2
    for board in result:
        assert "id" in board
        assert "name" in board
        assert len(board) == 2
