"""Модель отслеживаемого товара."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin
from shared.constants import Marketplace

if TYPE_CHECKING:
    from db.models.price_history import PriceHistory
    from db.models.user import User


class TrackedItem(Base, TimestampMixin):
    __tablename__ = "tracked_items"
    __table_args__ = (
        # один и тот же товар не дублируется у одного пользователя
        UniqueConstraint("user_id", "external_id", "marketplace", name="uq_user_item"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    marketplace: Mapped[Marketplace] = mapped_column(
        SAEnum(Marketplace, name="marketplace"), nullable=False
    )
    # external_id — артикул товара внутри маркетплейса (SKU/nm_id)
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Целевая цена: уведомляем, когда текущая опустится до/ниже неё
    target_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    last_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="items")
    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TrackedItem id={self.id} {self.marketplace}:{self.external_id}>"
