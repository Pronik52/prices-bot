"""Pydantic-схемы отслеживаемого товара и истории цен."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from shared.constants import Marketplace


class ItemCreate(BaseModel):
    # владелец задаётся по telegram_id — бот не знает внутренних id
    telegram_id: int
    url: str = Field(..., max_length=2048)
    target_price: Decimal | None = Field(default=None, ge=0)


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    marketplace: Marketplace
    external_id: str
    url: str
    title: str | None
    target_price: Decimal | None
    last_price: Decimal | None
    is_active: bool
    created_at: datetime


class PricePointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    price: Decimal
    recorded_at: datetime


class ItemPriceHistoryRead(BaseModel):
    item_id: int
    history: list[PricePointRead]
