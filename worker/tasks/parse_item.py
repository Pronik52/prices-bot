"""Задача на один товар: спарсить цену, записать историю, решить об уведомлении."""
from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

from api.services.notification_service import build_price_drop_message, should_notify
from db.models.notification_log import NotificationLog
from db.repositories.item_repository import ItemRepository
from db.session import session_scope
from parsers import extract_size_id, get_parser
from parsers.exceptions import ItemNotFound, ParserBlocked, PriceUnavailable
from shared.constants import NotificationStatus
from worker.celery_app import celery_app
from worker.tasks.send_notification import send_notification

logger = logging.getLogger(__name__)


@celery_app.task(
    name="worker.tasks.parse_item.parse_item",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def parse_item(self, item_id: int) -> str:  # noqa: ANN001
    with session_scope() as session:
        repo = ItemRepository(session)
        item = repo.get_by_id(item_id)
        if item is None or not item.is_active:
            return "skipped"

        parser = get_parser(item.marketplace)
        # выбранный вариант (размер) хранится в URL товара и влияет на цену
        size_id = extract_size_id(item.url)
        try:
            result = asyncio.run(parser.fetch_price(item.external_id, size_id))
        except ParserBlocked as exc:
            # временная блокировка — повторим позже (возможно, с другим прокси)
            logger.warning("Блокировка при парсинге item=%s: %s", item_id, exc)
            raise self.retry(exc=exc)
        except (ItemNotFound, PriceUnavailable) as exc:
            logger.info("Товар item=%s недоступен: %s", item_id, exc)
            return "unavailable"

        new_price = Decimal(result.price)

        # Заполняем название при первом успешном парсинге
        if not item.title and result.title:
            item.title = result.title

        # Проверяем условие уведомления ДО обновления last_price
        notify = should_notify(item, new_price)
        message = build_price_drop_message(item, new_price) if notify else None

        repo.add_price_point(item.id, float(new_price))
        item.last_price = float(new_price)

        if notify:
            telegram_id = item.owner.telegram_id
            session.add(
                NotificationLog(
                    user_id=item.user_id,
                    item_id=item.id,
                    price=float(new_price),
                    status=NotificationStatus.SENT,
                    message=message,
                )
            )
            # commit произойдёт при выходе из session_scope; ставим задачу отправки
            send_notification.delay(telegram_id, message)

    return "ok"
