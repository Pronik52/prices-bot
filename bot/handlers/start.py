"""Хендлеры /start и /help."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.client import ApiClient
from bot.keyboards import main_menu

router = Router()
logger = logging.getLogger(__name__)

WELCOME = (
    "👋 <b>Привет! Я слежу за ценами на маркетплейсах.</b>\n\n"
    "Пришли ссылку на товар с Wildberries или Ozon — и я сообщу, "
    "когда цена снизится до нужной.\n\n"
    "Выбери действие:"
)

HELP = (
    "<b>Как пользоваться</b>\n\n"
    "• «➕ Добавить товар» — пришли ссылку и (по желанию) целевую цену.\n"
    "• «📋 Мои товары» — список отслеживаемого, можно удалять.\n"
    "• «💎 Тарифы» — лимиты по количеству товаров.\n\n"
    "Как только цена достигнет цели — пришлю уведомление автоматически."
)


@router.message(Command("start"))
async def cmd_start(message: Message, api: ApiClient) -> None:
    user = message.from_user
    try:
        await api.register_user(user.id, user.username)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Не удалось зарегистрировать пользователя %s: %s", user.id, exc)
    await message.answer(WELCOME, reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP, reply_markup=main_menu())


@router.callback_query(F.data == "menu")
async def cb_menu(callback: CallbackQuery) -> None:
    """Возврат в главное меню (редактирует текущее сообщение)."""
    await callback.message.edit_text(WELCOME, reply_markup=main_menu())
    await callback.answer()
