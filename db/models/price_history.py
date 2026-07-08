"""История цен. Самая быстрорастущая таблица — на Стадии 2+ кандидат на
партиционирование по дате или вынос в time-series БД.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.tracked_item import TrackedItem


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("tracked_items.id", ondelete="CASCADE"), index=True, nullable=False
    )
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    item: Mapped["TrackedItem"] = relationship(back_populates="price_history")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PriceHistory item={self.item_id} price={self.price} at={self.recorded_at}>"
