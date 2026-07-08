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


def item_actions(item_id: int) -> InlineKeyboardMarkup:
    """Кнопка удаления конкретного товара."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Удалить", callback_data=f"del_item:{item_id}"
                )
            ]
        ]
    )


def cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✖️ Отмена", callback_data="cancel")]
        ]
    )
