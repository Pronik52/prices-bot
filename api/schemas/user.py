"""Pydantic-схемы пользователя."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from shared.constants import SubscriptionTier


class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: str | None
    subscription_tier: SubscriptionTier
    subscription_expires_at: datetime | None
    is_active: bool
    created_at: datetime


class SubscriptionUpdate(BaseModel):
    tier: SubscriptionTier
    # срок действия подписки; None = бессрочно (для FREE)
    expires_at: datetime | None = None
