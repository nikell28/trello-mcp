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
        due: str | None = None,
        pos: str | float | None = None,
    ) -> Card:
        """Создать карточку в указанном списке. Опциональные поля не отправляются если None."""
        params: dict[str, str | float] = {**self._auth, "idList": list_id, "name": name}
        if desc is not None:
            params["desc"] = desc
        if due is not None:
            params["due"] = due
        if pos is not None:
            params["pos"] = pos
        response = await self._client.post("/cards", params=params)
        self._raise_for_status(response)
        return Card.model_validate(response.json())

    async def move_card(
        self,
        card_id: str,
        list_id: str,
        pos: str | float | None = None,
    ) -> Card:
        """Переместить карточку в другой список. idList передаётся в теле запроса."""
        data: dict[str, str | float] = {"idList": list_id}
        if pos is not None:
            data["pos"] = pos
        response = await self._client.put(
            f"/cards/{card_id}",
            params=self._auth,
            data=data,
        )
        if response.status_code == 404:
            raise TrelloNotFoundError(f"Карточка не найдена (404): card_id={card_id!r}.")
        if response.status_code >= 400:
            raise TrelloAPIError(
                f"Ошибка Trello API ({response.status_code}): {response.text[:200]}"
            )
        return Card.model_validate(response.json())

    async def update_card(
        self,
        card_id: str,
        name: str | None = None,
        desc: str | None = None,
        due: str | None = None,
    ) -> Card:
        """Обновить поля карточки. Отправляются только переданные (не None) поля."""
        data: dict[str, str] = {}
        if name is not None:
            data["name"] = name
        if desc is not None:
            data["desc"] = desc
        if due is not None:
            data["due"] = due
        response = await self._client.put(
            f"/cards/{card_id}",
            params=self._auth,
            data=data,
        )
        if response.status_code == 404:
            raise TrelloNotFoundError(f"Карточка не найдена (404): card_id={card_id!r}.")
        if response.status_code >= 400:
            raise TrelloAPIError(
                f"Ошибка Trello API ({response.status_code}): {response.text[:200]}"
            )
        return Card.model_validate(response.json())

    async def get_labels(self) -> list[Label]:
        """Получить все labels управляемой доски."""
        response = await self._client.get(
            f"/boards/{self._settings.trello_board_id}/labels",
            params=self._auth,
        )
        self._raise_for_status(response)
        return [Label.model_validate(item) for item in response.json()]

    async def add_label_to_card(self, card_id: str, label_id: str) -> dict[str, str]:
        """Навесить label на карточку. Идемпотентно."""
        response = await self._client.post(
            f"/cards/{card_id}/idLabels",
            params=self._auth,
            data={"value": label_id},
        )
        if response.status_code == 404:
            raise TrelloNotFoundError(
                f"Карточка или label не найдены (404): card_id={card_id!r}, label_id={label_id!r}."
            )
        if response.status_code >= 400:
            raise TrelloAPIError(
                f"Ошибка Trello API ({response.status_code}): {response.text[:200]}"
            )
        return {"status": "ok", "card_id": card_id, "label_id": label_id}

    async def remove_label_from_card(self, card_id: str, label_id: str) -> dict[str, str]:
        """Снять label с карточки. 404 возвращается как читаемый результат (не исключение)."""
        response = await self._client.delete(
            f"/cards/{card_id}/idLabels/{label_id}",
            params=self._auth,
        )
        if response.status_code == 404:
            return {
                "status": "not_found",
                "detail": (
                    f"Label {label_id!r} не найден на карточке {card_id!r}"
                    " или карточка не существует."
                ),
            }
        if response.status_code >= 400:
            raise TrelloAPIError(
                f"Ошибка Trello API ({response.status_code}): {response.text[:200]}"
            )
        return {"status": "ok", "card_id": card_id, "label_id": label_id}

    async def update_position(self, card_id: str, pos: str | float) -> Card:
        """Изменить позицию карточки в её списке."""
        response = await self._client.put(
            f"/cards/{card_id}",
            params=self._auth,
            data={"pos": str(pos)},
        )
        if response.status_code == 404:
            raise TrelloNotFoundError(f"Карточка не найдена (404): card_id={card_id!r}.")
        if response.status_code >= 400:
            raise TrelloAPIError(
                f"Ошибка Trello API ({response.status_code}): {response.text[:200]}"
            )
        return Card.model_validate(response.json())

    async def add_comment(self, card_id: str, text: str) -> dict[str, str]:
        """Добавить текстовый комментарий к карточке."""
        response = await self._client.post(
            f"/cards/{card_id}/actions/comments",
            params={**self._auth, "text": text},
        )
        if response.status_code == 404:
            raise TrelloNotFoundError(f"Карточка не найдена (404): card_id={card_id!r}.")
        if response.status_code >= 400:
            raise TrelloAPIError(
                f"Ошибка Trello API ({response.status_code}): {response.text[:200]}"
            )
        data = response.json()
        return {"id": data["id"], "card_id": card_id, "text": text}

    async def get_comments(self, card_id: str) -> list[dict[str, object]]:
        """GET /cards/{card_id}/actions?filter=commentCard.

        Возвращает сырые actions Trello (без маппинга и сортировки).
        Преобразование в плоский результат и сортировка — в server.py.
        """
        response = await self._client.get(
            f"/cards/{card_id}/actions",
            params={**self._auth, "filter": "commentCard"},
        )
        if response.status_code == 401:
            raise TrelloAuthError(
                "Ошибка авторизации Trello (401): проверьте TRELLO_API_KEY и TRELLO_TOKEN."
            )
        if response.status_code == 404:
            raise TrelloNotFoundError(f"Карточка не найдена (404): card_id={card_id!r}.")
        if response.status_code >= 400:
            raise TrelloAPIError(
                f"Ошибка Trello API ({response.status_code}): {response.text[:200]}"
            )
        return list(response.json())
