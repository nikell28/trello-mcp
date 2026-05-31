"""Pydantic-модели ответов Trello API.

Модели описывают форму данных, которые инструменты будут возвращать агенту.
В Спринте 0 они уже настоящие (это контракт), но реально не наполняются —
инструменты возвращают заглушки.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Label(BaseModel):
    """Метка (label) на доске Trello."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Идентификатор label в Trello.")
    name: str = Field(description="Имя label (может быть пустым у цветных меток).")
    color: str | None = Field(
        default=None,
        description="Цвет label (green, yellow, red, ...). None — без цвета.",
    )


class List(BaseModel):
    """Список (колонка) на доске Trello."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Идентификатор списка в Trello.")
    name: str = Field(description="Имя списка.")
    closed: bool = Field(default=False, description="Список заархивирован.")
    pos: float = Field(default=0.0, description="Позиция списка на доске.")


class Card(BaseModel):
    """Карточка на доске Trello."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Идентификатор карточки в Trello.")
    name: str = Field(description="Имя (заголовок) карточки.")
    desc: str = Field(default="", description="Описание карточки.")
    id_list: str = Field(
        validation_alias="idList",
        serialization_alias="idList",
        description="Идентификатор списка, в котором лежит карточка.",
    )
    pos: float = Field(default=0.0, description="Позиция карточки в списке.")
    closed: bool = Field(default=False, description="Карточка заархивирована.")
    url: str | None = Field(default=None, description="Короткая ссылка на карточку.")
    labels: list[Label] = Field(
        default_factory=list,
        description="Метки, навешенные на карточку.",
    )
