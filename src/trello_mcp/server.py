"""FastMCP-сервер: регистрация 9 инструментов управления доской Trello.

Спринт 1: get_lists и get_cards реализованы — вызывают TrelloClient и
оборачивают ошибки в читаемый текст. Остальные инструменты остаются
заглушками. Конфиг и клиент создаются внутри каждого вызова инструмента,
чтобы сервер мог импортироваться без реальных кредов Trello.
"""

from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from trello_mcp import schemas
from trello_mcp.config import get_settings
from trello_mcp.errors import TrelloError
from trello_mcp.trello_client import TrelloClient

mcp = FastMCP("trello-mcp")

_STUB_STATUS = "not_implemented"


def _stub(tool: str) -> dict[str, str]:
    """Единый ответ-заглушка нереализованных инструментов."""
    return {
        "status": _STUB_STATUS,
        "tool": tool,
        "detail": "Инструмент ещё не реализован.",
    }


@mcp.tool()
async def get_lists() -> list[dict[str, str]] | str:
    """Вернуть все открытые списки (колонки) управляемой доски Trello.

    Доска берётся из конфигурации сервера (TRELLO_BOARD_ID). Параметров нет.
    Используй, чтобы увидеть структуру доски перед действиями над карточками.
    """
    try:
        settings = get_settings()
        async with TrelloClient(settings) as client:
            lists = await client.get_lists()
        return [{"id": lst.id, "name": lst.name} for lst in lists]
    except TrelloError as exc:
        return str(exc)


@mcp.tool()
async def get_cards() -> list[dict[str, object]] | str:
    """Вернуть все карточки управляемой доски Trello (урезанный набор полей).

    Доска берётся из конфигурации сервера (TRELLO_BOARD_ID). Параметров нет.
    Каждая карточка содержит: id, name, idList, labels.
    Используй перед созданием карточки, чтобы избежать дублей.
    """
    try:
        settings = get_settings()
        async with TrelloClient(settings) as client:
            cards = await client.get_cards()
        return [card.model_dump(by_alias=True) for card in cards]
    except TrelloError as exc:
        return str(exc)


@mcp.tool()
def create_card(
    list_id: Annotated[str, Field(description="Идентификатор списка, куда добавить карточку.")],
    name: Annotated[str, Field(description="Заголовок новой карточки (не пустой).")],
    desc: Annotated[str | None, Field(description="Описание карточки (опционально).")] = None,
    pos: Annotated[
        str | float | None,
        Field(description="Позиция: 'top', 'bottom' или неотрицательное число."),
    ] = None,
) -> dict[str, str]:
    """Создать карточку в списке.

    Аргументы:
        list_id: список назначения.
        name: заголовок карточки, обязателен и не может быть пустым.
        desc: описание карточки.
        pos: позиция — 'top', 'bottom' или число.
    """
    schemas.CreateCardArgs(list_id=list_id, name=name, desc=desc, pos=pos)
    return _stub("create_card")


@mcp.tool()
def move_card(
    card_id: Annotated[str, Field(description="Идентификатор перемещаемой карточки.")],
    list_id: Annotated[str, Field(description="Идентификатор списка назначения.")],
    pos: Annotated[
        str | float | None,
        Field(description="Позиция в новом списке: 'top', 'bottom' или число."),
    ] = None,
) -> dict[str, str]:
    """Переместить карточку в другой список (и опционально на позицию).

    Аргументы:
        card_id: перемещаемая карточка.
        list_id: список назначения.
        pos: позиция в новом списке — 'top', 'bottom' или число.
    """
    schemas.MoveCardArgs(card_id=card_id, list_id=list_id, pos=pos)
    return _stub("move_card")


@mcp.tool()
def update_card(
    card_id: Annotated[str, Field(description="Идентификатор обновляемой карточки.")],
    name: Annotated[str | None, Field(description="Новый заголовок (опционально).")] = None,
    desc: Annotated[str | None, Field(description="Новое описание (опционально).")] = None,
    closed: Annotated[
        bool | None,
        Field(description="Архивировать (true) или разархивировать (false) карточку."),
    ] = None,
) -> dict[str, str]:
    """Обновить поля карточки: заголовок, описание, статус архива.

    Аргументы:
        card_id: обновляемая карточка.
        name: новый заголовок (если задан, не пустой).
        desc: новое описание.
        closed: true — архивировать, false — разархивировать.
    """
    schemas.UpdateCardArgs(card_id=card_id, name=name, desc=desc, closed=closed)
    return _stub("update_card")


@mcp.tool()
def get_labels() -> dict[str, str]:
    """Вернуть все метки (labels) управляемой доски Trello.

    Доска берётся из конфигурации сервера. Параметров нет. Используй, чтобы
    узнать доступные id меток перед навешиванием на карточку.
    """
    schemas.GetLabelsArgs()
    return _stub("get_labels")


@mcp.tool()
def add_label_to_card(
    card_id: Annotated[str, Field(description="Идентификатор карточки.")],
    label_id: Annotated[str, Field(description="Идентификатор навешиваемого label.")],
) -> dict[str, str]:
    """Навесить метку (label) на карточку.

    Аргументы:
        card_id: карточка.
        label_id: идентификатор label, который нужно навесить.
    """
    schemas.AddLabelToCardArgs(card_id=card_id, label_id=label_id)
    return _stub("add_label_to_card")


@mcp.tool()
def remove_label_from_card(
    card_id: Annotated[str, Field(description="Идентификатор карточки.")],
    label_id: Annotated[str, Field(description="Идентификатор снимаемого label.")],
) -> dict[str, str]:
    """Снять метку (label) с карточки.

    Аргументы:
        card_id: карточка.
        label_id: идентификатор label, который нужно снять.
    """
    schemas.RemoveLabelFromCardArgs(card_id=card_id, label_id=label_id)
    return _stub("remove_label_from_card")


@mcp.tool()
def add_comment(
    card_id: Annotated[str, Field(description="Идентификатор карточки.")],
    text: Annotated[str, Field(description="Текст комментария (не пустой).")],
) -> dict[str, str]:
    """Добавить комментарий к карточке.

    Аргументы:
        card_id: карточка.
        text: текст комментария, не может быть пустым.
    """
    schemas.AddCommentArgs(card_id=card_id, text=text)
    return _stub("add_comment")
