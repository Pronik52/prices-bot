"""Периодическая задача-диспетчер: раскидывает по одной per-item задаче на товар.

Здесь заложена точка масштабирования: сам обход дешёвый (только чтение id из БД),
а тяжёлую работу (сетевые запросы к маркетплейсам) выполняют параллельные
per-item задачи parse_item, которые разгребает пул воркеров.
"""
from __future__ import annotations

import logging

from db.session import session_scope
from db.repositories.item_repository import ItemRepository
from worker.celery_app import celery_app
from worker.tasks.parse_item import parse_item

logger = logging.getLogger(__name__)


@celery_app.task(name="worker.tasks.check_prices.check_all_prices")
def check_all_prices() -> int:
    """Ставит в очередь задачу parse_item для каждого активного товара."""
    with session_scope() as session:
        repo = ItemRepository(session)
        item_ids = [item.id for item in repo.list_active()]

    for item_id in item_ids:
        parse_item.delay(item_id)

    logger.info("Запланирован обход %d товаров", len(item_ids))
    return len(item_ids)
