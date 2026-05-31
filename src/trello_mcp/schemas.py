"""Pydantic-модели аргументов инструментов — контракт вызова.

Это НЕ бизнес-логика, а валидация входных данных, поэтому в Спринте 0 модели
делаются настоящими: их тесты переживут спринт и будут жить дальше. Инструменты
сервера валидируют свои аргументы через эти модели перед обращением к Trello.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

_ALLOWED_POS_KEYWORDS = ("top", "bottom")


def _validate_pos(value: object) -> object:
    """Позиция в Trello: ключевое слово 'top'/'bottom' либо неотрицательное число."""
    if value is None:
        return None
    if isinstance(value, str):
        if value in _ALLOWED_POS_KEYWORDS:
            return value
        raise ValueError(
            f"pos строкой допускает только {_ALLOWED_POS_KEYWORDS}, получено: {value!r}"
        )
    if isinstance(value, bool):
        raise ValueError("pos не может быть булевым значением")
    if isinstance(value, (int, float)):
        if value < 0:
            raise ValueError("pos числом должно быть неотрицательным")
        return float(value)
    raise ValueError(
        f"pos должно быть 'top', 'bottom' или неотрицательным числом, получено: {value!r}"
    )


Position = Annotated[str | float, BeforeValidator(_validate_pos)]
"""Тип позиции карточки/списка: 'top', 'bottom' или неотрицательное число."""


def _validate_due(value: object) -> str | None:
    """Срок карточки: строка в ISO 8601 формате или None."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"due должен быть строкой в ISO-формате, получено: {value!r}")
    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"due должен быть в ISO-формате, получено: {value!r}")
    return value


DueDate = Annotated[str, BeforeValidator(_validate_due)]
"""Тип срока карточки: строка в ISO 8601 формате."""


class _ArgsModel(BaseModel):
    """База для моделей аргументов: запрещаем неизвестные поля."""

    model_config = ConfigDict(extra="forbid")


class GetCardsArgs(_ArgsModel):
    """Аргументы инструмента get_cards (нет параметров — доска берётся из конфига)."""


class CreateCardArgs(_ArgsModel):
    """Аргументы инструмента create_card."""

    list_id: str = Field(min_length=1, description="Идентификатор списка, куда создаётся карточка.")
    name: str = Field(min_length=1, description="Заголовок новой карточки (не пустой).")
    desc: str | None = Field(default=None, description="Описание карточки (опционально).")
    due: DueDate | None = Field(default=None, description="Срок в ISO-формате (опционально).")
    pos: Position | None = Field(default=None, description="Позиция: 'top', 'bottom' или число.")


class MoveCardArgs(_ArgsModel):
    """Аргументы инструмента move_card."""

    card_id: str = Field(min_length=1, description="Идентификатор перемещаемой карточки.")
    list_id: str = Field(min_length=1, description="Идентификатор списка назначения.")
    pos: Position | None = Field(default=None, description="Позиция в новом списке (опционально).")


class UpdateCardArgs(_ArgsModel):
    """Аргументы инструмента update_card."""

    card_id: str = Field(min_length=1, description="Идентификатор обновляемой карточки.")
    name: str | None = Field(
        default=None, min_length=1, description="Новый заголовок (опционально)."
    )
    desc: str | None = Field(default=None, description="Новое описание (опционально).")
    closed: bool | None = Field(
        default=None, description="Архивировать (True) / разархивировать (False)."
    )


class GetLabelsArgs(_ArgsModel):
    """Аргументы инструмента get_labels (нет параметров — доска берётся из конфига)."""


class GetListsArgs(_ArgsModel):
    """Аргументы инструмента get_lists (нет параметров — доска берётся из конфига)."""


class AddLabelToCardArgs(_ArgsModel):
    """Аргументы инструмента add_label_to_card."""

    card_id: str = Field(min_length=1, description="Идентификатор карточки.")
    label_id: str = Field(min_length=1, description="Идентификатор навешиваемого label.")


class RemoveLabelFromCardArgs(_ArgsModel):
    """Аргументы инструмента remove_label_from_card."""

    card_id: str = Field(min_length=1, description="Идентификатор карточки.")
    label_id: str = Field(min_length=1, description="Идентификатор снимаемого label.")


class AddCommentArgs(_ArgsModel):
    """Аргументы инструмента add_comment."""

    card_id: str = Field(min_length=1, description="Идентификатор карточки.")
    text: str = Field(min_length=1, description="Текст комментария (не пустой).")
