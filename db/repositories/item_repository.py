"""Доступ к данным отслеживаемых товаров и истории цен."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models.price_history import PriceHistory
from db.models.tracked_item import TrackedItem
from shared.constants import Marketplace


class ItemRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, item_id: int) -> TrackedItem | None:
        return self.session.get(TrackedItem, item_id)

    def get_for_user(self, item_id: int, user_id: int) -> TrackedItem | None:
        stmt = select(TrackedItem).where(
            TrackedItem.id == item_id, TrackedItem.user_id == user_id
        )
        return self.session.scalar(stmt)

    def find_duplicate(
        self, user_id: int, external_id: str, marketplace: Marketplace
    ) -> TrackedItem | None:
        stmt = select(TrackedItem).where(
            TrackedItem.user_id == user_id,
            TrackedItem.external_id == external_id,
            TrackedItem.marketplace == marketplace,
        )
        return self.session.scalar(stmt)

    def list_for_user(self, user_id: int) -> list[TrackedItem]:
        stmt = (
            select(TrackedItem)
            .where(TrackedItem.user_id == user_id)
            .order_by(TrackedItem.created_at.desc())
        )
        return list(self.session.scalars(stmt))

    def count_for_user(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(TrackedItem).where(
            TrackedItem.user_id == user_id
        )
        return self.session.scalar(stmt) or 0

    def list_active(self) -> list[TrackedItem]:
        """Все активные товары — для обхода планировщиком."""
        stmt = select(TrackedItem).where(TrackedItem.is_active.is_(True))
        return list(self.session.scalars(stmt))

    def create(
        self,
        user_id: int,
        marketplace: Marketplace,
        external_id: str,
        url: str,
        title: str | None = None,
        target_price: float | None = None,
    ) -> TrackedItem:
        item = TrackedItem(
            user_id=user_id,
            marketplace=marketplace,
            external_id=external_id,
            url=url,
            title=title,
            target_price=target_price,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def delete(self, item: TrackedItem) -> None:
        self.session.delete(item)

    # --- История цен ---

    def add_price_point(
        self, item_id: int, price: float, recorded_at: datetime | None = None
    ) -> PriceHistory:
        point = PriceHistory(item_id=item_id, price=price)
        if recorded_at is not None:
            point.recorded_at = recorded_at
        self.session.add(point)
        return point

    def get_price_history(
        self, item_id: int, limit: int = 100
    ) -> list[PriceHistory]:
        stmt = (
            select(PriceHistory)
            .where(PriceHistory.item_id == item_id)
            .order_by(PriceHistory.recorded_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))
