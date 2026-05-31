"""Точка входа: `python -m trello_mcp` и консольный скрипт `trello-mcp`.

Поднимает FastMCP-сервер по транспорту stdio. Логи настраиваются на stderr,
чтобы не засорять stdout, по которому идёт JSON-RPC.
"""

from __future__ import annotations

import os

from trello_mcp.config import configure_logging
from trello_mcp.server import mcp


def main() -> None:
    """Запустить stdio MCP-сервер."""
    configure_logging(os.environ.get("LOG_LEVEL", "INFO"))
    mcp.run()


if __name__ == "__main__":
    main()
