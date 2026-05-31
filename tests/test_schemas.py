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
    UpdateCardArgs,
    UpdatePositionArgs,
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


# ---------------------------------------------------------------------------
# TC-NAP: create_card validation
# ---------------------------------------------------------------------------


def test_tc_nap_01_3_empty_name_rejected() -> None:
    """TC-NAP-01-3 — Пустой name отклоняется валидацией без HTTP-запроса."""
    with pytest.raises(ValidationError):
        CreateCardArgs(list_id="l1", name="")


def test_tc_nap_02_3_invalid_due_rejected() -> None:
    """TC-NAP-02-3 — Невалидный формат due отклоняется валидацией."""
    with pytest.raises(ValidationError):
        CreateCardArgs(list_id="l1", name="Задача", due="завтра")


def test_tc_nap_02_3_valid_due_accepted() -> None:
    """TC-NAP-02-3 — Корректный ISO-формат due принимается."""
    args = CreateCardArgs(list_id="l1", name="Задача", due="2026-06-01T12:00:00")
    assert args.due == "2026-06-01T12:00:00"


def test_tc_nap_03_3_invalid_pos_rejected() -> None:
    """TC-NAP-03-3 — Невалидное значение pos отклоняется (допустимы top, bottom, число)."""
    with pytest.raises(ValidationError):
        CreateCardArgs(list_id="l1", name="Задача", pos="middle")


# ---------------------------------------------------------------------------
# TC-OBN-01: update_card validation (#инициатива-e4u7qx)
# ---------------------------------------------------------------------------


def test_tc_obn_01_3_update_card_without_fields_rejected() -> None:
    """TC-OBN-01-3 — Вызов без единого поля отклоняется валидацией."""
    with pytest.raises(ValidationError):
        UpdateCardArgs(card_id="c1")


def test_tc_obn_01_3_update_card_with_name_accepted() -> None:
    """TC-OBN-01-3 вспомогательный — с name валидация проходит."""
    args = UpdateCardArgs(card_id="c1", name="Новое имя")
    assert args.name == "Новое имя"
    assert args.due is None


# ---------------------------------------------------------------------------
# TC-OBN-05: update_position validation (#инициатива-e4u7qx)
# ---------------------------------------------------------------------------


def test_tc_obn_05_2_update_position_invalid_pos_rejected() -> None:
    """TC-OBN-05-2 — Невалидное значение pos отклоняется валидацией."""
    with pytest.raises(ValidationError):
        UpdatePositionArgs(card_id="c1", pos="середина")


def test_tc_obn_05_2_update_position_valid_pos_accepted() -> None:
    """TC-OBN-05-2 вспомогательный — допустимые значения pos принимаются."""
    assert UpdatePositionArgs(card_id="c1", pos="top").pos == "top"
    assert UpdatePositionArgs(card_id="c1", pos="bottom").pos == "bottom"
    assert UpdatePositionArgs(card_id="c1", pos=42).pos == 42.0
