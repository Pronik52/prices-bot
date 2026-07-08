"""Задача отправки уведомления в Telegram.

Отправляем напрямую через HTTP Bot API (httpx) — не тянем aiogram в воркер.
"""
from __future__ import annotations

import logging
import os

import httpx

from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org"


@celery_app.task(
    name="worker.tasks.send_notification.send_notification",
    bind=True,
    max_retries=5,
    default_retry_delay=30,
)
def send_notification(self, telegram_id: int, text: str) -> str:  # noqa: ANN001
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не задан — уведомление не отправлено")
        return "no_token"

    url = f"{_TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = httpx.post(url, json=payload, timeout=10.0)
    except httpx.HTTPError as exc:
        logger.warning("Ошибка сети при отправке в Telegram: %s", exc)
        raise self.retry(exc=exc)

    if resp.status_code == 429:
        # Telegram просит подождать — уважаем retry_after
        retry_after = int(resp.json().get("parameters", {}).get("retry_after", 30))
        raise self.retry(countdown=retry_after)
    if resp.status_code != 200:
        logger.error("Telegram вернул %s: %s", resp.status_code, resp.text)
        return "failed"

    return "sent"
