"""Журнал отправленных уведомлений — чтобы не спамить повторно."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from shared.constants import NotificationStatus


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("tracked_items.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # цена, при которой сработало уведомление
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(
            NotificationStatus,
            name="notification_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=NotificationStatus.SENT,
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<NotificationLog user={self.user_id} item={self.item_id} {self.status}>"
