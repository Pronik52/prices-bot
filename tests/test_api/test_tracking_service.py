"""Тесты бизнес-логики отслеживания на in-memory SQLite."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.services.tracking_service import (
    DuplicateItemError,
    InvalidItemUrlError,
    LimitReachedError,
    TrackingService,
)
from db.base import Base
import db.models  # noqa: F401  регистрирует таблицы
from db.repositories.user_repository import UserRepository
from shared.constants import SubscriptionTier, TIER_ITEM_LIMITS

WB_URL = "https://www.wildberries.ru/catalog/{}/detail.aspx"


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def test_add_item_ok(session):
    service = TrackingService(session)
    item = service.add_item(telegram_id=1, url=WB_URL.format(111))
    assert item.external_id == "111"
    assert item.marketplace.value == "wildberries"


def test_add_item_invalid_url(session):
    service = TrackingService(session)
    with pytest.raises(InvalidItemUrlError):
        service.add_item(telegram_id=1, url="https://example.com/x")


def test_add_item_duplicate(session):
    service = TrackingService(session)
    service.add_item(telegram_id=1, url=WB_URL.format(222))
    with pytest.raises(DuplicateItemError):
        service.add_item(telegram_id=1, url=WB_URL.format(222))


def test_limit_enforced_for_free_tier(session):
    service = TrackingService(session)
    limit = TIER_ITEM_LIMITS[SubscriptionTier.FREE]
    for i in range(limit):
        service.add_item(telegram_id=1, url=WB_URL.format(1000 + i))
    with pytest.raises(LimitReachedError):
        service.add_item(telegram_id=1, url=WB_URL.format(9999))


def test_remove_item(session):
    service = TrackingService(session)
    item = service.add_item(telegram_id=1, url=WB_URL.format(333))
    assert service.remove_item(telegram_id=1, item_id=item.id) is True
    assert service.list_items(telegram_id=1) == []


def test_premium_has_higher_limit(session):
    repo = UserRepository(session)
    user = repo.get_or_create(telegram_id=1)
    user.subscription_tier = SubscriptionTier.PREMIUM
    session.commit()
    service = TrackingService(session)
    # добавим больше, чем лимит free — не должно упасть
    for i in range(TIER_ITEM_LIMITS[SubscriptionTier.FREE] + 1):
        service.add_item(telegram_id=1, url=WB_URL.format(2000 + i))
    assert len(service.list_items(telegram_id=1)) == (
        TIER_ITEM_LIMITS[SubscriptionTier.FREE] + 1
    )
