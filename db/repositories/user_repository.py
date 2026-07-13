"""Доступ к данным пользователей. Без бизнес-логики — только запросы."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models.tracked_item import TrackedItem
from db.models.user import User
from shared.constants import SubscriptionTier


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return self.session.scalar(stmt)

    def create(
        self,
        telegram_id: int,
        username: str | None = None,
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> User:
        user = User(telegram_id=telegram_id, username=username, subscription_tier=tier)
        self.session.add(user)
        self.session.flush()  # чтобы получить user.id
        return user

    def get_or_create(self, telegram_id: int, username: str | None = None) -> User:
        user = self.get_by_telegram_id(telegram_id)
        if user is None:
            user = self.create(telegram_id, username)
        elif username and user.username != username:
            user.username = username
        return user

    def list_all(self) -> list[User]:
        return list(self.session.scalars(select(User)))

    # --- Агрегаты и пагинация для админки ---

    def count_all(self) -> int:
        return self.session.scalar(select(func.count()).select_from(User)) or 0

    def count_created_since(self, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(User)
            .where(User.created_at >= since)
        )
        return self.session.scalar(stmt) or 0

    def list_with_item_counts(
        self, offset: int, limit: int
    ) -> list[tuple[User, int]]:
        """Страница пользователей (в порядке регистрации) вместе с числом их
        товаров. Один запрос: LEFT JOIN + GROUP BY, чтобы не делать N+1 подсчётов.
        """
        stmt = (
            select(User, func.count(TrackedItem.id))
            .outerjoin(TrackedItem, TrackedItem.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
            .offset(offset)
            .limit(limit)
        )
        return [(user, count) for user, count in self.session.execute(stmt)]
