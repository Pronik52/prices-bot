"""Pydantic-схемы админки: сводка и постраничный список пользователей."""
from __future__ import annotations

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Сводные метрики для главного экрана админки."""

    total_users: int
    total_items: int
    active_items: int
    new_users_7d: int


class AdminUserRow(BaseModel):
    """Строка списка пользователей: идентификатор + число товаров."""

    telegram_id: int
    username: str | None
    item_count: int


class UsersPage(BaseModel):
    """Одна страница списка пользователей с метаданными пагинации.

    `page` и `total_pages` всегда >= 1; сервис клампит запрошенную страницу в
    допустимый диапазон, поэтому клиент может слать любое число.
    """

    users: list[AdminUserRow]
    page: int
    total_pages: int
    total_users: int
