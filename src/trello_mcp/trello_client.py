"""Клиент Trello REST API.

Спринт 1: реализованы get_lists() и get_cards(). Остальные методы остаются
заглушками до соответствующих спринтов. Ошибки HTTP маппируются в доменные
исключения из errors.py.
"""

from __future__ import annotations

from types import TracebackType

import httpx

from trello_mcp.config import Settings
from trello_mcp.errors import TrelloAPIError, TrelloAuthError, TrelloNotFoundError
from trello_mcp.models import Card, CardBrief, Label, List


class TrelloClient:
    """Тонкий async-клиент над Trello REST API (Спринт 0 — заглушка)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._auth = {
            "key": settings.trello_api_key,
            "token": settings.trello_token,
        }
        self._client = httpx.AsyncClient(
            base_url=settings.trello_api_base,
            timeout=httpx.Timeout(10.0),
        )

    async def aclose(self) -> None:
        """Закрыть нижележащий HTTP-клиент."""
        await self._client.aclose()

    async def __aenter__(self) -> TrelloClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Преобразовать HTTP-ошибку в доменное исключение с читаемым сообщением."""
        if response.status_code == 401:
            raise TrelloAuthError(
                "Ошибка авторизации Trello (401): проверьте TRELLO_API_KEY и TRELLO_TOKEN."
            )
        if response.status_code == 404:
            raise TrelloNotFoundError(
                f"Ресурс не найден (404): board_id={self._settings.trello_board_id!r}."
            )
        if response.status_code >= 400:
            raise TrelloAPIError(
                f"Ошибка Trello API ({response.status_code}): {response.text[:200]}"
            )

    async def get_lists(self) -> list[List]:
        """Получить все открытые списки (колонки) управляемой доски."""
        response = await self._client.get(
            f"/boards/{self._settings.trello_board_id}/lists",
            params={**self._auth, "filter": "open"},
        )
        self._raise_for_status(response)
        return [List.model_validate(item) for item in response.json()]

    async def get_cards(self) -> list[CardBrief]:
        """Получить все карточки управляемой доски (урезанный набор полей)."""
        response = await self._client.get(
            f"/boards/{self._settings.trello_board_id}/cards",
            params={**self._auth, "fields": "id,name,idList,labels"},
        )
        self._raise_for_status(response)
        return [CardBrief.model_validate(item) for item in response.json()]

    async def create_card(
        self,
        list_id: str,
        name: str,
        desc: str | None = None,
        pos: str | float | None = None,
    ) -> Card:
        raise NotImplementedError("Stub: реализуется в Спринте 1")

    async def move_card(
        self,
        card_id: str,
        list_id: str,
        pos: str | float | None = None,
    ) -> Card:
        raise NotImplementedError("Stub: реализуется в Спринте 1")

    async def update_card(
        self,
        card_id: str,
        name: str | None = None,
        desc: str | None = None,
        closed: bool | None = None,
    ) -> Card:
        raise NotImplementedError("Stub: реализуется в Спринте 1")

    async def get_labels(self) -> list[Label]:
        raise NotImplementedError("Stub: реализуется в Спринте 1")

    async def add_label_to_card(self, card_id: str, label_id: str) -> Card:
        raise NotImplementedError("Stub: реализуется в Спринте 1")

    async def remove_label_from_card(self, card_id: str, label_id: str) -> Card:
        raise NotImplementedError("Stub: реализуется в Спринте 1")

    async def add_comment(self, card_id: str, text: str) -> dict[str, str]:
        raise NotImplementedError("Stub: реализуется в Спринте 1")
