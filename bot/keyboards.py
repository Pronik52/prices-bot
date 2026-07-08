"""Inline-клавиатуры бота."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить товар", callback_data="add_item")
    builder.button(text="📋 Мои товары", callback_data="list_items")
    builder.button(text="💎 Тарифы", callback_data="show_tiers")
    builder.adjust(1)
    return builder.as_markup()


def items_list(items: list[dict]) -> InlineKeyboardMarkup:
    """Одна клавиатура на весь список: по кнопке удаления на товар + «В меню».

    Всё в одном сообщении, которое затем редактируется — без спама новыми
    сообщениями.
    """
    builder = InlineKeyboardBuilder()
    for it in items:
        title = it.get("title") or f"Товар {it['external_id']}"
        builder.button(text=f"🗑 {title[:28]}", callback_data=f"del_item:{it['id']}")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✖️ Отмена", callback_data="cancel")]
        ]
    )
