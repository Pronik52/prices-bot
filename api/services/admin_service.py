"""Бизнес-логика админки: сводные метрики и постраничный список пользователей.

Слой не зависит от FastAPI — принимает готовую сессию и работает с репозиториями,
поэтому переиспользуется и в роутерах, и в тестах.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import ceil

from sqlalchemy.orm import Session

from api.schemas.admin import AdminUserRow, DashboardStats, UsersPage
from db.repositories.item_repository import ItemRepository
from db.repositories.user_repository import UserRepository

# Товаров на страницу списка пользователей.
DEFAULT_PAGE_SIZE = 10
# Окно для метрики «новых пользователей».
NEW_USERS_WINDOW = timedelta(days=7)


class AdminService:
    def __init__(self, session: Session) -> None:
        self.users = UserRepository(session)
        self.items = ItemRepository(session)

    def dashboard(self) -> DashboardStats:
        since = datetime.now(timezone.utc) - NEW_USERS_WINDOW
        return DashboardStats(
            total_users=self.users.count_all(),
            total_items=self.items.count_all(),
            active_items=self.items.count_active(),
            new_users_7d=self.users.count_created_since(since),
        )

    def users_page(
        self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE
    ) -> UsersPage:
        total_users = self.users.count_all()
        total_pages = max(1, ceil(total_users / page_size))
        # клампим запрошенную страницу — клиент может прислать что угодно
        page = max(1, min(page, total_pages))

        rows = self.users.list_with_item_counts(
            offset=(page - 1) * page_size, limit=page_size
        )
        return UsersPage(
            users=[
                AdminUserRow(
                    telegram_id=user.telegram_id,
                    username=user.username,
                    item_count=count,
                )
                for user, count in rows
            ],
            page=page,
            total_pages=total_pages,
            total_users=total_users,
        )
