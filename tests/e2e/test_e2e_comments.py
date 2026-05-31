"""E2E тест чтения комментариев против реальной доски Trello.

TC-CHT-01-8 — на реальной карточке считываются комментарии в хронологическом
порядке с корректными авторами, текстами, датами (#инициатива-c6r4kp).

По умолчанию пропускается: требует реальных кредов Trello.
Запуск: TRELLO_E2E_BOARD_ID=... TRELLO_E2E_CARD_ID=... pytest -m e2e
"""

from __future__ import annotations

import os

import pytest

from trello_mcp.config import Settings
from trello_mcp.server import _map_comment_action, _sort_comments_by_created_at
from trello_mcp.trello_client import TrelloClient

pytestmark = pytest.mark.e2e


def _e2e_settings() -> Settings:
    board_id = os.environ.get("TRELLO_E2E_BOARD_ID")
    if not board_id:
        pytest.skip("e2e требует реальных кредов Trello (TRELLO_E2E_BOARD_ID не задан)")
    return Settings(trello_board_id=board_id)  # type: ignore[call-arg]


async def test_tc_cht_01_8_real_dialog_read() -> None:
    """TC-CHT-01-8 — Реальный диалог на карточке считывается в хронологическом порядке.

    Нужна карточка с двумя комментариями от разных авторов. Если второй аккаунт
    недоступен — допускается карточка с двумя комментариями от одного автора:
    проверяется порядок и базовый маппинг.
    """
    # Given: реальная доска, известен id карточки с комментариями
    card_id = os.environ.get("TRELLO_E2E_CARD_ID")
    if not card_id:
        pytest.skip("e2e требует TRELLO_E2E_CARD_ID")
    settings = _e2e_settings()

    async with TrelloClient(settings) as client:
        # When: считываются и маппятся комментарии карточки
        actions = await client.get_comments(card_id=card_id)

    comments = _sort_comments_by_created_at([_map_comment_action(a) for a in actions])

    # Then: получены минимум два комментария с корректными полями, по возрастанию даты
    assert len(comments) >= 2, "Ожидалось минимум два комментария на тестовой карточке"
    for comment in comments:
        assert comment["id"]
        assert comment["author"]
        assert comment["text"]
        assert comment["created_at"]
    created_dates = [c["created_at"] for c in comments]
    assert created_dates == sorted(created_dates), "Комментарии должны идти от старых к новым"
