"""Доменные исключения для работы с Trello API.

Спринт 0: только каркас иерархии исключений. Реальная обработка ответов и
ошибок Trello появится в Спринте 1 — тела классов пока пустые.
"""


class TrelloError(Exception):
    """Базовое исключение для любых ошибок взаимодействия с Trello."""


class TrelloConfigError(TrelloError):
    """Некорректная или отсутствующая конфигурация (env-переменные)."""


class TrelloAuthError(TrelloError):
    """Ошибка авторизации: неверный API key или token (HTTP 401)."""


class TrelloNotFoundError(TrelloError):
    """Запрошенный ресурс (доска, список, карточка, label) не найден (HTTP 404)."""


class TrelloRateLimitError(TrelloError):
    """Превышен лимит запросов к Trello API (HTTP 429)."""


class TrelloAPIError(TrelloError):
    """Прочая ошибка Trello API (неожиданный статус ответа)."""
