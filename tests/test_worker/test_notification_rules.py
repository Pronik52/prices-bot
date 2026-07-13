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


def test_significant_drop_no_target_notifies():
    # цель не задана, снижение ровно на 2% — значимое, уведомляем
    assert should_notify(_item(target=None, last=1000), Decimal(980)) is True


def test_small_drop_no_target_no_notify():
    # цель не задана, снижение меньше 2% — незначимое, молчим
    assert should_notify(_item(target=None, last=1000), Decimal(990)) is False


def test_target_reached_notifies():
    # цель задана и достигнута — уведомляем даже при снижении меньше 2%
    assert should_notify(_item(target=995, last=1000), Decimal(995)) is True


def test_target_not_reached_no_notify():
    # цель задана, цена снизилась значимо, но цели не достигла — молчим
    assert should_notify(_item(target=800, last=1000), Decimal(900)) is False
