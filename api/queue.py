"""Отправка задач в очередь Celery из API-слоя.

API не выполняет парсинг сам — он лишь ставит задачу в очередь (Redis),
а разгребают её воркеры. Здесь — лёгкий продюсер: он шлёт задачу по имени
и не импортирует код воркера (никакой связности api -> worker).
"""
from __future__ import annotations

import logging

from celery import Celery

from api.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
# Продюсер без include: send_task по строковому имени не требует регистрации задачи
_producer = Celery(broker=_settings.celery_broker_url)

PARSE_ITEM_TASK = "worker.tasks.parse_item.parse_item"


def enqueue_parse_item(item_id: int) -> bool:
    """Ставит немедленный парсинг товара. Не роняет запрос при недоступном брокере.

    Возвращает True, если задача поставлена в очередь.
    """
    try:
        _producer.send_task(PARSE_ITEM_TASK, args=[item_id])
        return True
    except Exception as exc:  # noqa: BLE001 — товар уже сохранён, парсинг подхватит beat
        logger.warning("Не удалось поставить parse_item для item=%s: %s", item_id, exc)
        return False
