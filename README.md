# Trello MCP Server

Мост между AI-агентом и Trello: набор MCP-инструментов, через которые агент
управляет доской на естественном языке — читает списки и карточки, создаёт,
двигает между списками, навешивает метки, комментирует.

> **Статус: Спринт 1+ — реализация инструментов.**
> 12 инструментов реализованы и полностью функциональны. Все проходят линт,
> типизацию (mypy strict) и тесты. Пакет собирается и готов к использованию.

## Инструменты (контракт)

| Инструмент                | Назначение                                  |
| ------------------------- | ------------------------------------------- |
| `get_boards`              | Все открытые доски пользователя (опционально с фильтром по названию) |
| `get_lists`               | Списки (колонки) доски                       |
| `get_cards`               | Карточки указанного списка                   |
| `create_card`             | Создать карточку                             |
| `move_card`               | Переместить карточку в другой список          |
| `update_card`             | Обновить поля карточки                        |
| `get_labels`              | Метки (labels) доски                          |
| `add_label_to_card`       | Навесить метку на карточку                     |
| `remove_label_from_card`  | Снять метку с карточки                         |
| `add_comment`             | Добавить комментарий к карточке                |
| `get_comments`            | Прочитать комментарии карточки (от старых к новым) |

## Требования

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) — менеджер зависимостей и запуска

## Установка

```bash
git clone https://github.com/nikell28/trello-mcp
cd trello-mcp
uv sync --frozen
```

## Переменные окружения

Скопируй `.env.example` в `.env` и заполни:

| Переменная         | Обяз. | По умолчанию                  | Описание                       |
| ------------------ | :---: | ----------------------------- | ------------------------------ |
| `TRELLO_API_KEY`   |   ✓   | —                             | API key Trello                 |
| `TRELLO_TOKEN`     |   ✓   | —                             | API token Trello               |
| `TRELLO_BOARD_ID`  |       | `None`                        | Дефолтная доска (опционально)   |
| `TRELLO_API_BASE`  |       | `https://api.trello.com/1`    | Базовый URL REST API            |
| `LOG_LEVEL`        |       | `INFO`                        | Уровень логирования             |

При отсутствии обязательных переменных (`TRELLO_API_KEY`, `TRELLO_TOKEN`) сервер
падает с явной ошибкой валидации. `TRELLO_BOARD_ID` — необязательная переменная:
если не задана, `board_id` нужно передавать в инструменты `get_lists`, `get_labels`,
`get_cards` явно.

## Multi-board usage

По умолчанию `get_lists`, `get_labels`, `get_cards` работают с доской из `TRELLO_BOARD_ID`.
Чтобы указать другую доску для конкретного вызова, передай `board_id` явно:

```python
# Получить списки конкретной доски
result = await client.call_tool("get_lists", {"board_id": "BOARD_ID_HERE"})

# Дефолтное поведение (использует TRELLO_BOARD_ID из конфига)
result = await client.call_tool("get_lists", {})
```

Если `board_id` не передан и `TRELLO_BOARD_ID` не задан — инструмент вернёт ошибку.

## Запуск

```bash
# Как установленный скрипт (после uv sync) или напрямую через uvx:
uvx --from . trello-mcp

# Или модулем:
uv run python -m trello_mcp
```

Сервер работает по транспорту **stdio**: stdout занят JSON-RPC, все логи идут в
**stderr**.

### Инспектор инструментов (MCP Inspector)

```bash
uv run mcp dev src/trello_mcp/server.py
```

Откроется веб-инспектор, где видны 12 инструментов с их схемами.

## Подключение к OpenClaw

Добавь сервер в конфиг `mcp.servers` (stdio):

```json
{
  "mcp": {
    "servers": {
      "trello": {
        "command": "uvx",
        "args": ["--from", "/абсолютный/путь/к/trello-mcp", "trello-mcp"],
        "env": {
          "TRELLO_API_KEY": "...",
          "TRELLO_TOKEN": "...",
          "TRELLO_BOARD_ID": "..."
        }
      }
    }
  }
}
```

### Troubleshooting

- **OpenClaw молчит в чате при ошибке сервера.** Если инструмент недоступен или
  сервер упал, в чате не будет внятной ошибки — диагностика только в логе
  gateway/хоста MCP. Смотри stderr процесса сервера.
- **`uvx trello-mcp` не стартует.** Проверь точку входа локально:
  `uvx --from . trello-mcp`. Часто ломается именно entry point.
- **Сервер «зависает» сразу после старта.** Это нормально для stdio: сервер ждёт
  JSON-RPC по stdin. Используй MCP Inspector или хост-клиент.

## Разработка

```bash
uv run ruff check .          # линт
uv run ruff format --check . # формат
uv run mypy src              # типы (strict)
uv run pytest -m "not e2e"   # тесты (без e2e)
uv build                     # сборка пакета
```

CI (GitHub Actions) гоняет всё это на Python 3.12 и 3.13 при каждом push и PR.
e2e-тесты по умолчанию пропускаются (нужны реальные креды) и в CI не запускаются.

## Лицензия

[MIT](LICENSE)
