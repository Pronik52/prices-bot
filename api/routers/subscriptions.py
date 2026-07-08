"""Роуты управления подписками.

На Стадии 1 — без реальных платежей: только смена тарифа (например, вручную
или из будущего платёжного вебхука). Интеграция с ЮKassa/Stripe — Стадия 2.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, verify_internal_token
from api.schemas.user import SubscriptionUpdate, UserRead
from db.repositories.user_repository import UserRepository
from shared.constants import TIER_ITEM_LIMITS

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
    dependencies=[Depends(verify_internal_token)],
)


@router.get("/tiers")
def list_tiers() -> dict[str, int]:
    """Доступные тарифы и их лимиты по количеству товаров."""
    return {tier.value: limit for tier, limit in TIER_ITEM_LIMITS.items()}


@router.put("/{telegram_id}", response_model=UserRead)
def update_subscription(
    telegram_id: int,
    payload: SubscriptionUpdate,
    session: Session = Depends(get_db),
) -> UserRead:
    repo = UserRepository(session)
    user = repo.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    user.subscription_tier = payload.tier
    user.subscription_expires_at = payload.expires_at
    session.commit()
    session.refresh(user)
    return user
