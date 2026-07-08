"""Импорт всех моделей в одном месте — нужно для Alembic autogenerate."""
from db.models.notification_log import NotificationLog
from db.models.price_history import PriceHistory
from db.models.tracked_item import TrackedItem
from db.models.user import User

__all__ = ["User", "TrackedItem", "PriceHistory", "NotificationLog"]
