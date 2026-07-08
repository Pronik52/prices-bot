"""Бизнес-правила отслеживания товаров: лимиты по тарифу, валидация ссылок.

Слой не зависит от FastAPI — принимает готовую сессию и работает с репозиториями,
поэтому переиспользуется и в роутерах, и в тестах.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from db.models.tracked_item import TrackedItem
from db.models.user import User
from db.repositories.item_repository import ItemRepository
from db.repositories.user_repository import UserRepository
from parsers import extract_item_ref
from parsers.exceptions import InvalidUrl, UnsupportedMarketplace
from shared.constants import TIER_ITEM_LIMITS


class TrackingError(Exception):
    """Базовая ошибка бизнес-логики отслеживания (маппится в HTTP 4xx)."""


class LimitReachedError(TrackingError):
    pass


class DuplicateItemError(TrackingError):
    pass


class InvalidItemUrlError(TrackingError):
    pass


class TrackingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.items = ItemRepository(session)
        self.users = UserRepository(session)

    def add_item(
        self,
        telegram_id: int,
        url: str,
        target_price: Decimal | None = None,
    ) -> TrackedItem:
        user = self.users.get_or_create(telegram_id)

        # 1. Валидация ссылки и определение маркетплейса/артикула
        try:
            ref = extract_item_ref(url)
        except (UnsupportedMarketplace, InvalidUrl) as exc:
            raise InvalidItemUrlError(str(exc)) from exc

        # 2. Проверка дубликата
        if self.items.find_duplicate(user.id, ref.external_id, ref.marketplace):
            raise DuplicateItemError("Этот товар уже отслеживается")

        # 3. Проверка лимита по тарифу
        limit = TIER_ITEM_LIMITS[user.subscription_tier]
        if self.items.count_for_user(user.id) >= limit:
            raise LimitReachedError(
                f"Достигнут лимит тарифа: {limit} товаров. "
                f"Оформите Premium, чтобы отслеживать больше."
            )

        item = self.items.create(
            user_id=user.id,
            marketplace=ref.marketplace,
            external_id=ref.external_id,
            url=url,
            target_price=float(target_price) if target_price is not None else None,
        )
        self.session.commit()
        return item

    def remove_item(self, telegram_id: int, item_id: int) -> bool:
        user = self.users.get_by_telegram_id(telegram_id)
        if user is None:
            return False
        item = self.items.get_for_user(item_id, user.id)
        if item is None:
            return False
        self.items.delete(item)
        self.session.commit()
        return True

    def list_items(self, telegram_id: int) -> list[TrackedItem]:
        user = self.users.get_by_telegram_id(telegram_id)
        if user is None:
            return []
        return self.items.list_for_user(user.id)

    def remaining_slots(self, user: User) -> int:
        limit = TIER_ITEM_LIMITS[user.subscription_tier]
        return max(0, limit - self.items.count_for_user(user.id))
