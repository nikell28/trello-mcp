"""Тесты валидации схем аргументов.

Схемы в Спринте 0 уже настоящие, поэтому эти тесты переживут спринт. Проверяем
позитивные кейсы и явные негативные: пустой name, невалидный pos.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from trello_mcp.schemas import (
    AddCommentArgs,
    CreateCardArgs,
    MoveCardArgs,
)


def test_create_card_valid_minimal() -> None:
    args = CreateCardArgs(list_id="l1", name="Задача")
    assert args.name == "Задача"
    assert args.pos is None


@pytest.mark.parametrize("pos", ["top", "bottom", 0, 0.0, 42, 1024.5])
def test_create_card_valid_pos(pos: str | float) -> None:
    args = CreateCardArgs(list_id="l1", name="Задача", pos=pos)
    assert args.pos is not None


def test_create_card_empty_name_rejected() -> None:
    with pytest.raises(ValidationError):
        CreateCardArgs(list_id="l1", name="")


def test_create_card_invalid_pos_string_rejected() -> None:
    with pytest.raises(ValidationError):
        CreateCardArgs(list_id="l1", name="Задача", pos="middle")


def test_create_card_negative_pos_rejected() -> None:
    with pytest.raises(ValidationError):
        CreateCardArgs(list_id="l1", name="Задача", pos=-1)


def test_create_card_empty_list_id_rejected() -> None:
    with pytest.raises(ValidationError):
        CreateCardArgs(list_id="", name="Задача")


def test_move_card_invalid_pos_rejected() -> None:
    with pytest.raises(ValidationError):
        MoveCardArgs(card_id="c1", list_id="l1", pos="sideways")


def test_add_comment_empty_text_rejected() -> None:
    with pytest.raises(ValidationError):
        AddCommentArgs(card_id="c1", text="")
