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
