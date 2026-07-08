"""Единая настройка логирования для всех процессов (api, bot, worker)."""
from __future__ import annotations

import logging
import os
import sys


def setup_logging(level: str | None = None) -> None:
    """Конфигурирует корневой логгер. Идемпотентно."""
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()

    root = logging.getLogger()
    if root.handlers:  # уже настроено — не дублируем хендлеры
        root.setLevel(log_level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(log_level)

    # Приглушаем слишком болтливые библиотеки
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
