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


def test_no_target_no_notify():
    assert should_notify(_item(target=None), Decimal(100)) is False


def test_price_above_target_no_notify():
    assert should_notify(_item(target=1000, last=1500), Decimal(1200)) is False


def test_price_crosses_down_notifies():
    assert should_notify(_item(target=1000, last=1500), Decimal(950)) is True


def test_first_time_below_target_notifies():
    assert should_notify(_item(target=1000, last=None), Decimal(900)) is True


def test_already_below_does_not_spam():
    # прошлая цена уже была не выше цели — повторно не уведомляем
    assert should_notify(_item(target=1000, last=900), Decimal(880)) is False
