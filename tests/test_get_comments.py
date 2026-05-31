"""Тесты инструмента get_comments (US-CHT-01, #инициатива-c6r4kp).

TC-CHT-01-2,3,4 — unit на чистые функции маппинга/сортировки в server.py.
TC-CHT-01-1,5,6,7 — integration через respx на полный путь
(HTTP → клиент → маппинг → отсортированный результат).
"""

from __future__ import annotations

import httpx
import respx

from trello_mcp.config import Settings
from trello_mcp.server import _map_comment_action, _sort_comments_by_created_at, get_comments

# ---------------------------------------------------------------------------
# Хелперы тестовых данных: actions так, как их отдаёт Trello
# (по умолчанию — в обратном хронологическом порядке).
# ---------------------------------------------------------------------------


def _action(action_id: str, text: str, date: str, full_name: str, username: str) -> dict:
    return {
        "id": action_id,
        "type": "commentCard",
        "date": date,
        "data": {"text": text},
        "memberCreator": {"fullName": full_name, "username": username},
    }


# ---------------------------------------------------------------------------
# TC-CHT-01-2 — unit: сортировка от старых к новым
# ---------------------------------------------------------------------------


def test_tc_cht_01_2_comments_sorted_oldest_first() -> None:
    """TC-CHT-01-2 — Комментарии упорядочены по created_at по возрастанию."""
    # Given: три комментария в обратном хронологическом порядке (как Trello)
    comments = [
        {"id": "c3", "author": "A", "text": "третий", "created_at": "2026-03-03T10:00:00.000Z"},
        {"id": "c2", "author": "A", "text": "второй", "created_at": "2026-02-02T10:00:00.000Z"},
        {"id": "c1", "author": "A", "text": "первый", "created_at": "2026-01-01T10:00:00.000Z"},
    ]
    # When: сортируется чистой функцией
    result = _sort_comments_by_created_at(comments)
    # Then: порядок по created_at по возрастанию
    assert [c["created_at"] for c in result] == [
        "2026-01-01T10:00:00.000Z",
        "2026-02-02T10:00:00.000Z",
        "2026-03-03T10:00:00.000Z",
    ]
    assert [c["id"] for c in result] == ["c1", "c2", "c3"]


# ---------------------------------------------------------------------------
# TC-CHT-01-3 — unit: маппинг полей Trello → инструмент
# ---------------------------------------------------------------------------


def test_tc_cht_01_3_field_mapping() -> None:
    """TC-CHT-01-3 — Результат содержит ровно id, author=fullName, text, created_at=date."""
    # Given: один action с полным набором полей
    action = _action(
        action_id="cmt-1",
        text="Привет",
        date="2026-01-01T12:00:00.000Z",
        full_name="Иван Иванов",
        username="ivan",
    )
    # When: маппится в результат
    result = _map_comment_action(action)
    # Then: ровно четыре поля с корректными значениями
    assert result == {
        "id": "cmt-1",
        "author": "Иван Иванов",
        "text": "Привет",
        "created_at": "2026-01-01T12:00:00.000Z",
    }


# ---------------------------------------------------------------------------
# TC-CHT-01-4 — unit: фолбэк автора на username
# ---------------------------------------------------------------------------


def test_tc_cht_01_4_author_fallback_to_username() -> None:
    """TC-CHT-01-4 — Если fullName отсутствует, в author подставляется username."""
    # Given: action без fullName, только username
    action = {
        "id": "cmt-2",
        "type": "commentCard",
        "date": "2026-01-02T12:00:00.000Z",
        "data": {"text": "Без имени"},
        "memberCreator": {"username": "user42"},
    }
    # When: маппится в результат
    result = _map_comment_action(action)
    # Then: author = username
    assert result["author"] == "user42"


# ---------------------------------------------------------------------------
# TC-CHT-01-1 — integration: возвращает все комментарии, корректный путь и filter
# ---------------------------------------------------------------------------


async def test_tc_cht_01_1_returns_all_comments(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-CHT-01-1 — Три commentCard actions → три комментария; путь и filter корректны."""
    # Given: замокан GET /cards/{id}/actions, отвечает тремя actions
    actions = [
        _action("c3", "третий", "2026-03-03T10:00:00.000Z", "Б", "b"),
        _action("c2", "второй", "2026-02-02T10:00:00.000Z", "А", "a"),
        _action("c1", "первый", "2026-01-01T10:00:00.000Z", "А", "a"),
    ]
    route = respx_mock.get("/cards/card-xyz/actions").mock(
        return_value=httpx.Response(200, json=actions)
    )
    # When: вызывается get_comments
    result = await get_comments(card_id="card-xyz")
    # Then: три комментария, каждый с полями id, author, text, created_at
    assert isinstance(result, list)
    assert len(result) == 3
    for comment in result:
        assert set(comment.keys()) == {"id", "author", "text", "created_at"}
    # запрос ушёл на корректный путь с filter=commentCard
    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["filter"] == "commentCard"


# ---------------------------------------------------------------------------
# TC-CHT-01-5 — integration: пустой массив actions → пустой список
# ---------------------------------------------------------------------------


async def test_tc_cht_01_5_empty_comments_returns_empty_list(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-CHT-01-5 — Карточка без комментариев → пустой список, без ошибки."""
    # Given: замокан endpoint, возвращает пустой массив
    respx_mock.get("/cards/card-empty/actions").mock(return_value=httpx.Response(200, json=[]))
    # When: вызывается get_comments
    result = await get_comments(card_id="card-empty")
    # Then: пустой список, ошибка не поднята
    assert result == []


# ---------------------------------------------------------------------------
# TC-CHT-01-6 — integration: несуществующая карточка (404) → читаемая ошибка
# ---------------------------------------------------------------------------


async def test_tc_cht_01_6_nonexistent_card_readable_message(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-CHT-01-6 — 404 возвращает читаемое сообщение об отсутствии карточки."""
    # Given: замокан endpoint, 404
    respx_mock.get("/cards/nonexistent/actions").mock(
        return_value=httpx.Response(404, text="Card not found")
    )
    # When: вызывается get_comments с несуществующим id
    result = await get_comments(card_id="nonexistent")
    # Then: читаемое сообщение об ошибке (строка), карточка не найдена
    assert isinstance(result, str)
    assert "nonexistent" in result


# ---------------------------------------------------------------------------
# TC-CHT-01-7 — integration: ошибка авторизации (401) → читаемая ошибка
# ---------------------------------------------------------------------------


async def test_tc_cht_01_7_auth_error_readable_message(
    settings: Settings, respx_mock: respx.MockRouter
) -> None:
    """TC-CHT-01-7 — 401 возвращает читаемое сообщение об ошибке авторизации."""
    # Given: замокан endpoint, 401
    respx_mock.get("/cards/card-xyz/actions").mock(
        return_value=httpx.Response(401, text="invalid token")
    )
    # When: вызывается get_comments
    result = await get_comments(card_id="card-xyz")
    # Then: читаемое сообщение об ошибке авторизации
    assert isinstance(result, str)
    assert "авториз" in result.lower()
