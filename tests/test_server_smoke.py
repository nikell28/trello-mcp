"""Smoke-тест сервера: импортируется, FastMCP создаётся, ровно 10 инструментов."""

from __future__ import annotations

from trello_mcp.server import mcp

EXPECTED_TOOLS = {
    "get_lists",
    "get_cards",
    "create_card",
    "move_card",
    "update_card",
    "get_labels",
    "add_label_to_card",
    "remove_label_from_card",
    "update_position",
    "add_comment",
}


async def test_server_registers_exactly_ten_tools() -> None:
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    assert len(tools) == 10
    assert names == EXPECTED_TOOLS


async def test_every_tool_has_description() -> None:
    tools = await mcp.list_tools()
    for tool in tools:
        assert tool.description, f"У инструмента {tool.name} нет docstring/описания"
