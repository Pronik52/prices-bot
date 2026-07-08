"""Формирование текста уведомлений и правила «когда уведомлять»."""
from __future__ import annotations

from decimal import Decimal

from db.models.tracked_item import TrackedItem


def should_notify(item: TrackedItem, new_price: Decimal) -> bool:
    """Уведомляем, если задана целевая цена и новая цена опустилась до/ниже неё.

    Дополнительно защищаемся от повторного спама: не уведомляем, если прошлая
    зафиксированная цена уже была не выше целевой (значит, уже уведомляли).
    """
    if item.target_price is None:
        return False
    target = Decimal(item.target_price)
    if new_price > target:
        return False
    # Новая цена достигла цели. Уведомляем только если это «свежее» пересечение:
    # прошлая цена была выше целевой (или её ещё не было).
    if item.last_price is None:
        return True
    return Decimal(item.last_price) > target


def build_price_drop_message(item: TrackedItem, new_price: Decimal) -> str:
    title = item.title or f"Товар {item.external_id}"
    old = f"{Decimal(item.last_price):.0f} ₽" if item.last_price is not None else "—"
    lines = [
        "🔥 <b>Цена снизилась!</b>",
        "",
        f"<b>{title}</b>",
        f"Было: {old}",
        f"Стало: <b>{new_price:.0f} ₽</b>",
    ]
    if item.target_price is not None:
        lines.append(f"Ваша цель: {Decimal(item.target_price):.0f} ₽")
    lines.append("")
    lines.append(f'<a href="{item.url}">Открыть на маркетплейсе</a>')
    return "\n".join(lines)
