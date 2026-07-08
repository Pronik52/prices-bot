"""Доступ к данным пользователей. Без бизнес-логики — только запросы."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

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
