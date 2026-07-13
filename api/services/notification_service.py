"""Формирование текста уведомлений и правила «когда уведомлять»."""
from __future__ import annotations

from decimal import Decimal

from db.models.tracked_item import TrackedItem

# Порог «значимого» снижения, когда целевая цена не задана: 2%.
SIGNIFICANT_DROP_RATIO = Decimal("0.02")


def should_notify(item: TrackedItem, new_price: Decimal) -> bool:
    """Решает, нужно ли слать уведомление о новой цене.

    Первый парсинг (когда прошлой цены ещё нет) уведомлением не сопровождается —
    сравнивать не с чем. Рост цены игнорируем. При снижении:

    * если задана целевая цена — сигналим, когда цена достигла цели (≤ цели);
    * если цель не задана — только при значимом снижении (не меньше 2%),
      чтобы не спамить на каждое копеечное колебание.
    """
    if item.last_price is None:
        return False
    last = Decimal(item.last_price)
    if new_price >= last:
        return False

    if item.target_price is not None:
        return new_price <= Decimal(item.target_price)

    return (last - new_price) / last >= SIGNIFICANT_DROP_RATIO


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
