"""Общие перечисления и константы, используемые всеми слоями системы."""
from __future__ import annotations

from enum import Enum


class Marketplace(str, Enum):
    """Поддерживаемые маркетплейсы. Значение совпадает с ключом парсера."""

    WILDBERRIES = "wildberries"
    OZON = "ozon"


class SubscriptionTier(str, Enum):
    """Тарифы подписки."""

    FREE = "free"
    PREMIUM = "premium"


# Лимиты на количество отслеживаемых товаров по тарифу.
TIER_ITEM_LIMITS: dict[SubscriptionTier, int] = {
    SubscriptionTier.FREE: 5,
    SubscriptionTier.PREMIUM: 100,
}


class NotificationStatus(str, Enum):
    """Статус отправленного уведомления."""

    SENT = "sent"
    FAILED = "failed"


def marketplace_from_url(url: str) -> Marketplace | None:
    """Определяет маркетплейс по домену ссылки. None — если не поддерживается."""
    low = url.lower()
    if "wildberries.ru" in low or "wb.ru" in low:
        return Marketplace.WILDBERRIES
    if "ozon.ru" in low:
        return Marketplace.OZON
    return None
