"""Тесты правил уведомлений."""
from __future__ import annotations

from decimal import Decimal

from api.services.notification_service import should_notify
from db.models.tracked_item import TrackedItem
from shared.constants import Marketplace


def _item(target=None, last=None) -> TrackedItem:
    return TrackedItem(
        user_id=1,
        marketplace=Marketplace.WILDBERRIES,
        external_id="1",
        url="http://x",
        target_price=target,
        last_price=last,
    )


def test_no_previous_price_no_notify():
    # первый парсинг — сравнивать не с чем, не уведомляем
    assert should_notify(_item(last=None), Decimal(100)) is False


def test_price_increase_no_notify():
    assert should_notify(_item(last=1000), Decimal(1200)) is False


def test_price_unchanged_no_notify():
    assert should_notify(_item(last=1000), Decimal(1000)) is False


def test_any_price_drop_notifies():
    assert should_notify(_item(last=1500), Decimal(1450)) is True


def test_price_drop_notifies_regardless_of_target():
    # целевая цена не задана, но цена снизилась — уведомляем
    assert should_notify(_item(target=None, last=1000), Decimal(900)) is True
