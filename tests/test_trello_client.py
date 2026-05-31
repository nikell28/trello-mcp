"""Интеграционные тесты клиента Trello REST API.

TC-OBZ-01-1..5 — инструмент get_lists (US-OBZ-01).
TC-OBZ-02-1..4 — инструмент get_cards (US-OBZ-02).
TC-NAP-01-1,2,4 — create_card базовое (US-NAP-01).
TC-NAP-02-1,2   — create_card с desc/due (US-NAP-02).
TC-NAP-03-1,2   — create_card с pos (US-NAP-03).

Мок на уровне HTTP через respx; проверяются и построение запроса,
и обработка ответа / ошибочных статусов.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from trello_mcp.config import Settings
from trello_mcp.errors import TrelloAPIError, TrelloAuthError, TrelloNotFoundError
from trello_mcp.trello_client import TrelloClient

BOARD_ID = "test-board"


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[TrelloClient]:
    async with TrelloClient(settings) as c:
        yield c


# ---------------------------------------------------------------------------
# TC-OBZ-01: get_lists
# ---------------------------------------------------------------------------


async def test_tc_obz_01_1_returns_all_lists(
    client: TrelloClient, respx_mock: respx.MockRouter
) -> None:
    """TC-OBZ-01-1 — Возврат всех списков доски."""
    # Given: замокан GET /boards/{id}/lists, возвращает 3 списка
    respx_mock.get(f"/boards/{BOARD_ID}/lists").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "l1", "name": "To Do", "closed": False, "pos": 1},
                {"id": "l2", "name": "In Progress", "closed": False, "pos": 2},
                {"id": "l3", "name": "Done", "closed": False, "pos": 3},
            ],
        )
    )
    # When: вызывается инструмент get_lists
    lists = await client.get_lists()
    # Then: возвращаются 3 списка, каждый содержит id и name
    assert len(lists) == 3
    assert all(lst.id and lst.name for lst in lists)


async def test_tc_obz_01_2_correct_url_and_auth(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-OBZ-01-2 — Корректный URL и авторизация в запросе."""
    # Given: замокан Trello API, board id и креды из конфига
    route = respx_mock.get(f"/boards/{BOARD_ID}/lists").mock(
        return_value=httpx.Response(200, json=[])
    )
    async with TrelloClient(settings) as client:
        # When: вызывается get_lists
        await client.get_lists()
    # Then: запрос уходит на /boards/{board_id}/lists с key и token в query
    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["key"] == "test-key"
    assert params["token"] == "test-token"


async def test_tc_obz_01_3_filter_open_in_request(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-OBZ-01-3 — Archived-списки исключены по умолчанию (filter=open)."""
    # Given: замокан API
    route = respx_mock.get(f"/boards/{BOARD_ID}/lists").mock(
        return_value=httpx.Response(200, json=[])
    )
    async with TrelloClient(settings) as client:
        # When: вызывается get_lists
        await client.get_lists()
    # Then: в запросе присутствует filter=open
    params = dict(route.calls.last.request.url.params)
    assert params["filter"] == "open"


async def test_tc_obz_01_4_401_raises_auth_error(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-OBZ-01-4 — Ошибка 401 возвращается читаемым текстом (TrelloAuthError)."""
    # Given: замокан API, возвращает 401
    respx_mock.get(f"/boards/{BOARD_ID}/lists").mock(
        return_value=httpx.Response(401, text="Unauthorized")
    )
    async with TrelloClient(settings) as client:
        # When/Then: поднимается TrelloAuthError, не бросается необработанное исключение
        with pytest.raises(TrelloAuthError) as exc_info:
            await client.get_lists()
    # Сообщение читаемое
    assert str(exc_info.value)


async def test_tc_obz_01_5_404_raises_not_found_error(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-OBZ-01-5 — Ошибка 404 (несуществующий board) возвращается читаемым текстом."""
    # Given: замокан API, возвращает 404
    respx_mock.get(f"/boards/{BOARD_ID}/lists").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    async with TrelloClient(settings) as client:
        # When/Then: поднимается TrelloNotFoundError, не бросается необработанное исключение
        with pytest.raises(TrelloNotFoundError) as exc_info:
            await client.get_lists()
    assert str(exc_info.value)


# ---------------------------------------------------------------------------
# TC-OBZ-02: get_cards
# ---------------------------------------------------------------------------


async def test_tc_obz_02_1_returns_all_cards(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-OBZ-02-1 — Возврат всех карточек доски."""
    # Given: замокан GET /boards/{id}/cards, возвращает 5 карточек
    respx_mock.get(f"/boards/{BOARD_ID}/cards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": f"c{i}", "name": f"Card {i}", "idList": "l1", "labels": []}
                for i in range(5)
            ],
        )
    )
    async with TrelloClient(settings) as client:
        # When: вызывается get_cards
        cards = await client.get_cards()
    # Then: возвращаются 5 карточек
    assert len(cards) == 5


async def test_tc_obz_02_2_only_required_fields_returned(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-OBZ-02-2 — Урезанный набор полей в ответе (только id, name, idList, labels)."""
    # Given: замокан API, карточка содержит много полей
    respx_mock.get(f"/boards/{BOARD_ID}/cards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "c1",
                    "name": "Card",
                    "idList": "l1",
                    "labels": [],
                    "desc": "some description",
                    "badges": {"votes": 0},
                    "idMembers": [],
                    "closed": False,
                    "url": "https://trello.com/c/test",
                    "pos": 65536,
                }
            ],
        )
    )
    async with TrelloClient(settings) as client:
        # When: вызывается get_cards
        cards = await client.get_cards()
    # Then: каждая карточка содержит только id, name, idList, labels
    card_dict = cards[0].model_dump(by_alias=True)
    assert set(card_dict.keys()) == {"id", "name", "idList", "labels"}


async def test_tc_obz_02_3_labels_included(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-OBZ-02-3 — Labels включены в выдачу."""
    # Given: замокан API, у карточки есть 2 label
    respx_mock.get(f"/boards/{BOARD_ID}/cards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "c1",
                    "name": "Card",
                    "idList": "l1",
                    "labels": [
                        {"id": "lb1", "name": "Bug", "color": "red"},
                        {"id": "lb2", "name": "Feature", "color": "green"},
                    ],
                }
            ],
        )
    )
    async with TrelloClient(settings) as client:
        # When: вызывается get_cards
        cards = await client.get_cards()
    # Then: поле labels карточки содержит оба label
    assert len(cards[0].labels) == 2


async def test_tc_obz_02_4_500_raises_api_error(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-OBZ-02-4 — Ошибка API возвращается читаемым текстом (TrelloAPIError)."""
    # Given: замокан API, возвращает 500
    respx_mock.get(f"/boards/{BOARD_ID}/cards").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    async with TrelloClient(settings) as client:
        # When/Then: поднимается TrelloAPIError, не бросается необработанное исключение
        with pytest.raises(TrelloAPIError) as exc_info:
            await client.get_cards()
    assert str(exc_info.value)


# ---------------------------------------------------------------------------
# TC-NAP-01: create_card — базовое создание карточки
# ---------------------------------------------------------------------------

_CARD_RESPONSE = {
    "id": "abc123",
    "name": "Новая задача",
    "idList": "list-001",
    "desc": "",
    "pos": 65536.0,
    "closed": False,
    "url": "https://trello.com/c/abc123",
    "labels": [],
}


async def test_tc_nap_01_1_card_created_in_list(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-NAP-01-1 — Запрос уходит с idList и name; карточка создаётся в указанном списке."""
    # Given: замокан POST /cards, возвращает созданную карточку
    route = respx_mock.post("/cards").mock(return_value=httpx.Response(200, json=_CARD_RESPONSE))
    async with TrelloClient(settings) as client:
        # When: вызывается create_card с idList и name
        card = await client.create_card(list_id="list-001", name="Новая задача")
    # Then: запрос уходит с переданными idList и name
    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["idList"] == "list-001"
    assert params["name"] == "Новая задача"
    assert card.id_list == "list-001"


async def test_tc_nap_01_2_returns_card_id(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-NAP-01-2 — Инструмент возвращает id "abc123" созданной карточки."""
    # Given: замокан API, возвращает карточку с id="abc123"
    respx_mock.post("/cards").mock(return_value=httpx.Response(200, json=_CARD_RESPONSE))
    async with TrelloClient(settings) as client:
        # When: вызывается create_card
        card = await client.create_card(list_id="list-001", name="Новая задача")
    # Then: возвращается id "abc123"
    assert card.id == "abc123"


async def test_tc_nap_01_4_invalid_list_id_raises_readable_error(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-NAP-01-4 — Несуществующий idList возвращает читаемое сообщение об ошибке."""
    # Given: замокан API, возвращает 400 на невалидный idList
    respx_mock.post("/cards").mock(return_value=httpx.Response(400, text="invalid id"))
    async with TrelloClient(settings) as client:
        # When/Then: поднимается TrelloAPIError с читаемым сообщением
        with pytest.raises(TrelloAPIError) as exc_info:
            await client.create_card(list_id="nonexistent", name="Задача")
    assert str(exc_info.value)


# ---------------------------------------------------------------------------
# TC-NAP-02: create_card — desc и due
# ---------------------------------------------------------------------------


async def test_tc_nap_02_1_desc_and_due_sent_in_request(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-NAP-02-1 — desc и due попадают в запрос в корректном формате."""
    # Given: замокан POST /cards
    route = respx_mock.post("/cards").mock(
        return_value=httpx.Response(
            200,
            json={**_CARD_RESPONSE, "desc": "Описание задачи"},
        )
    )
    async with TrelloClient(settings) as client:
        # When: вызывается create_card с desc и due (ISO-дата)
        await client.create_card(
            list_id="list-001",
            name="Новая задача",
            desc="Описание задачи",
            due="2026-06-01T12:00:00",
        )
    # Then: параметры запроса содержат desc и due
    params = dict(route.calls.last.request.url.params)
    assert params["desc"] == "Описание задачи"
    assert params["due"] == "2026-06-01T12:00:00"


async def test_tc_nap_02_2_desc_and_due_optional(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-NAP-02-2 — Без desc и due поля не отправляются в запросе."""
    # Given: замокан API
    route = respx_mock.post("/cards").mock(return_value=httpx.Response(200, json=_CARD_RESPONSE))
    async with TrelloClient(settings) as client:
        # When: вызывается create_card без desc и due
        await client.create_card(list_id="list-001", name="Новая задача")
    # Then: поля desc и due отсутствуют в запросе
    params = dict(route.calls.last.request.url.params)
    assert "desc" not in params
    assert "due" not in params


# ---------------------------------------------------------------------------
# TC-NAP-03: create_card — pos
# ---------------------------------------------------------------------------


async def test_tc_nap_03_1_pos_top_sent_in_request(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-NAP-03-1 — pos=top передаётся в параметры запроса."""
    # Given: замокан POST /cards
    route = respx_mock.post("/cards").mock(return_value=httpx.Response(200, json=_CARD_RESPONSE))
    async with TrelloClient(settings) as client:
        # When: вызывается create_card с pos="top"
        await client.create_card(list_id="list-001", name="Новая задача", pos="top")
    # Then: параметры запроса содержат pos=top
    params = dict(route.calls.last.request.url.params)
    assert params["pos"] == "top"


async def test_tc_nap_03_2_without_pos_field_not_sent(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-NAP-03-2 — Без pos поле не отправляется (поведение Trello по умолчанию)."""
    # Given: замокан API
    route = respx_mock.post("/cards").mock(return_value=httpx.Response(200, json=_CARD_RESPONSE))
    async with TrelloClient(settings) as client:
        # When: вызывается create_card без pos
        await client.create_card(list_id="list-001", name="Новая задача")
    # Then: поле pos отсутствует в запросе
    params = dict(route.calls.last.request.url.params)
    assert "pos" not in params
