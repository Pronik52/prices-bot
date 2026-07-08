"""Инициализация Celery. Брокер и бэкенд — Redis."""
from __future__ import annotations

import os

from celery import Celery

from shared.logging_config import setup_logging

setup_logging()

celery_app = Celery(
    "price_tracker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    include=[
        "worker.tasks.check_prices",
        "worker.tasks.parse_item",
        "worker.tasks.send_notification",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,  # задача подтверждается после выполнения (устойчивость к падениям)
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
)

# Расписание Celery Beat
from worker.beat_schedule import beat_schedule  # noqa: E402

celery_app.conf.beat_schedule = beat_schedule
