"""Точка входа Telegram-бота (aiogram 3, long polling)."""
from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from bot.client import ApiClient
from bot.handlers import build_router
from shared.logging_config import setup_logging

logger = logging.getLogger(__name__)


async def on_error(event: ErrorEvent) -> bool:
    """Глобальный обработчик: логируем и всегда уведомляем пользователя,
    чтобы непойманное исключение не оборачивалось молчанием бота.
    """
    logger.exception("Необработанная ошибка в апдейте: %s", event.exception)
    update = event.update
    try:
        if update.message is not None:
            await update.message.answer("⚠️ Что-то пошло не так. Попробуйте позже.")
        elif update.callback_query is not None:
            await update.callback_query.answer(
                "Что-то пошло не так, попробуйте позже", show_alert=True
            )
    except Exception:  # noqa: BLE001 — не даём обработчику ошибок упасть самому
        logger.exception("Не удалось уведомить пользователя об ошибке")
    return True


async def main() -> None:
    setup_logging()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не задан в окружении")

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # HTTP-клиент к API инжектируется в хендлеры по имени аргумента `api`
    api = ApiClient()
    dp["api"] = api

    dp.include_router(build_router())
    dp.errors.register(on_error)

    logger.info("Бот запущен (long polling)")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await api.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
