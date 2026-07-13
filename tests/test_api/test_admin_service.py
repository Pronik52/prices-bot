"""Тесты админской бизнес-логики (сводка + пагинация) на in-memory SQLite."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.services.admin_service import AdminService
from db.base import Base
import db.models  # noqa: F401  регистрирует таблицы
from db.repositories.item_repository import ItemRepository
from db.repositories.user_repository import UserRepository
from shared.constants import Marketplace


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


def _make_user(session, telegram_id, *, items=0, inactive=0, created_at=None):
    """Создаёт пользователя с `items` товарами, из них `inactive` неактивных."""
    user = UserRepository(session).create(telegram_id=telegram_id)
    if created_at is not None:
        user.created_at = created_at
    irepo = ItemRepository(session)
    for i in range(items):
        item = irepo.create(
            user_id=user.id,
            marketplace=Marketplace.WILDBERRIES,
            external_id=f"{telegram_id}-{i}",
            url="http://example/x",
        )
        if i < inactive:
            item.is_active = False
    session.flush()
    return user


def test_dashboard_counts(session):
    _make_user(session, 1, items=3)
    _make_user(session, 2, items=2, inactive=1)
    stats = AdminService(session).dashboard()
    assert stats.total_users == 2
    assert stats.total_items == 5
    assert stats.active_items == 4


def test_dashboard_new_users_window(session):
    now = datetime.now(timezone.utc)
    _make_user(session, 1, created_at=now)
    _make_user(session, 2, created_at=now - timedelta(days=10))  # старый — вне окна
    stats = AdminService(session).dashboard()
    assert stats.total_users == 2
    assert stats.new_users_7d == 1


def test_users_page_pagination_and_counts(session):
    for tg in range(1, 26):  # 25 пользователей, id по возрастанию
        _make_user(session, tg, items=(2 if tg == 1 else 0))

    svc = AdminService(session)

    first = svc.users_page(page=1)
    assert first.total_users == 25
    assert first.total_pages == 3
    assert first.page == 1
    assert len(first.users) == 10
    # порядок регистрации: первый в списке — самый ранний, с 2 товарами
    assert first.users[0].telegram_id == 1
    assert first.users[0].item_count == 2

    last = svc.users_page(page=3)
    assert last.page == 3
    assert len(last.users) == 5


def test_users_page_clamps_out_of_range(session):
    for tg in range(1, 26):
        _make_user(session, tg)
    page = AdminService(session).users_page(page=99)
    assert page.page == 3  # прижато к последней странице
    assert len(page.users) == 5


def test_users_page_empty(session):
    page = AdminService(session).users_page(page=1)
    assert page.total_users == 0
    assert page.total_pages == 1
    assert page.page == 1
    assert page.users == []
