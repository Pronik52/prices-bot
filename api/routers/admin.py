"""Роуты админки: сводка и постраничный список пользователей.

Эндпоинты доступны только по внутренней сети и защищены X-Internal-Token, как и
остальной API. Кто из Telegram-пользователей считается админом — решает бот
(по списку ADMIN_TELEGRAM_IDS), API этим не занимается.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db, verify_internal_token
from api.schemas.admin import DashboardStats, UsersPage
from api.services.admin_service import DEFAULT_PAGE_SIZE, AdminService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_internal_token)],
)


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(session: Session = Depends(get_db)) -> DashboardStats:
    return AdminService(session).dashboard()


@router.get("/users", response_model=UsersPage)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    session: Session = Depends(get_db),
) -> UsersPage:
    return AdminService(session).users_page(page=page, page_size=page_size)
