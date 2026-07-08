"""Формирование текста уведомлений и правила «когда уведомлять»."""
from __future__ import annotations

from decimal import Decimal

from db.models.tracked_item import TrackedItem


def should_notify(item: TrackedItem, new_price: Decimal) -> bool:
    """Уведомляем при любом снижении цены относительно последней зафиксированной.

    Первый парсинг (когда прошлой цены ещё нет) уведомлением не сопровождается —
    сравнивать не с чем. Далее сигналим на каждое падение цены, независимо от того,
    задана ли целевая цена.
    """
    if item.last_price is None:
        return False
    return new_price < Decimal(item.last_price)


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
