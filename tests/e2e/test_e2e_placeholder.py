"""Плейсхолдер e2e-теста.

Закрепляет маркер `e2e` и инфраструктуру запуска против реальной доски. По
умолчанию пропускается: реальных кредов нет, а CI запускается с `-m "not e2e"`.
Реальные e2e появятся в Спринте 1 (в т.ч. проверка поведения labels — главный
риск проекта).
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e


def test_e2e_placeholder() -> None:
    if not os.environ.get("TRELLO_E2E_BOARD_ID"):
        pytest.skip("e2e требует реальных кредов Trello (TRELLO_E2E_BOARD_ID не задан)")
    raise AssertionError("e2e-тесты будут реализованы в Спринте 1")
