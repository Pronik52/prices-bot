"""Клавиатуры бота."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Тексты кнопок прикреплённого меню — используются и в клавиатуре, и в фильтрах хендлеров.
BTN_ADD = "➕ Добавить товар"
BTN_LIST = "📋 Мои товары"


def main_menu() -> ReplyKeyboardMarkup:
    """Постоянное меню внизу экрана.

    is_persistent=True держит клавиатуру прикреплённой, поэтому нужные действия
    всегда под рукой — их не нужно искать в переписке после потока уведомлений.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_ADD), KeyboardButton(text=BTN_LIST)]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери действие или пришли ссылку на товар",
    )


def items_list(items: list[dict]) -> InlineKeyboardMarkup:
    """Кнопки удаления по товару на всё сообщение со списком."""
    builder = InlineKeyboardBuilder()
    for it in items:
        title = it.get("title") or f"Товар {it['external_id']}"
        builder.button(text=f"🗑 {title[:28]}", callback_data=f"del_item:{it['id']}")
    builder.adjust(1)
    return builder.as_markup()


def cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✖️ Отмена", callback_data="cancel")]
        ]
    )
