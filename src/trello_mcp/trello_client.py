"""Каркас клиента Trello REST API.

Спринт 0: класс существует, конструктор готовит httpx.AsyncClient, но методы
не реализованы — каждый бросает NotImplementedError. Реальные вызовы и разбор
ответов появятся в Спринте 1 (по TDD, с respx-моками).
"""

from __future__ import annotations

from types import TracebackType

import httpx

from trello_mcp.config import Settings
from trello_mcp.models import Card, Label, List


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

    async def get_lists(self) -> list[List]:
        raise NotImplementedError("Stub: реализуется в Спринте 1")

    async def get_cards(self, list_id: str) -> list[Card]:
        raise NotImplementedError("Stub: реализуется в Спринте 1")

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
