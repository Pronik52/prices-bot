"""Расписание периодических задач Celery Beat."""
from __future__ import annotations

import os

# Интервал полного обхода всех товаров (по умолчанию раз в час)
PRICE_CHECK_INTERVAL = float(os.getenv("PRICE_CHECK_INTERVAL", "3600"))

beat_schedule = {
    "check-all-prices": {
        "task": "worker.tasks.check_prices.check_all_prices",
        "schedule": PRICE_CHECK_INTERVAL,
    },
}
