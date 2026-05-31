"""E2E тесты создания карточек против реальной доски Trello.

TC-NAP-01-5 — создать карточку, проверить через get_cards.

По умолчанию пропускаются: требуют реальных кредов Trello.
Запуск: TRELLO_E2E_BOARD_ID=... pytest -m e2e
"""

from __future__ import annotations

import os

import pytest

from trello_mcp.config import Settings
from trello_mcp.trello_client import TrelloClient

pytestmark = pytest.mark.e2e


def _e2e_settings() -> Settings:
    board_id = os.environ.get("TRELLO_E2E_BOARD_ID")
    if not board_id:
        pytest.skip("e2e требует реальных кредов Trello (TRELLO_E2E_BOARD_ID не задан)")
    return Settings(trello_board_id=board_id)  # type: ignore[call-arg]


async def test_tc_nap_01_5_card_appears_on_board() -> None:
    """TC-NAP-01-5 — Созданная карточка присутствует в выдаче get_cards."""
    # Given: реальная тестовая доска, известный idList из env
    list_id = os.environ.get("TRELLO_E2E_LIST_ID")
    if not list_id:
        pytest.skip("e2e требует TRELLO_E2E_LIST_ID")
    settings = _e2e_settings()
    card_name = "E2E TC-NAP-01-5: create_card test"

    async with TrelloClient(settings) as client:
        # When: вызывается create_card, затем get_cards
        created = await client.create_card(list_id=list_id, name=card_name)
        cards = await client.get_cards()

    # Then: созданная карточка присутствует в выдаче get_cards
    card_ids = {card.id for card in cards}
    assert created.id in card_ids, f"Карточка {created.id} не найдена на доске"


async def test_tc_prd_01_4_card_changes_list() -> None:
    """TC-PRD-01-4 — Карточка реально меняет список (#инициатива-p7m3xw)."""
    # Given: реальная доска, карточка в списке A, известен id списка B
    list_id_a = os.environ.get("TRELLO_E2E_LIST_ID")
    list_id_b = os.environ.get("TRELLO_E2E_LIST_ID_B")
    if not list_id_a or not list_id_b:
        pytest.skip("e2e требует TRELLO_E2E_LIST_ID и TRELLO_E2E_LIST_ID_B")
    settings = _e2e_settings()

    async with TrelloClient(settings) as client:
        created = await client.create_card(
            list_id=list_id_a, name="E2E TC-PRD-01-4: move_card test"
        )
        # When: вызывается move_card в список B, затем get_cards
        await client.move_card(card_id=created.id, list_id=list_id_b)
        cards = await client.get_cards()

    # Then: карточка имеет idList = список B
    card_map = {card.id: card for card in cards}
    assert created.id in card_map, f"Карточка {created.id} не найдена на доске"
    assert card_map[created.id].id_list == list_id_b
