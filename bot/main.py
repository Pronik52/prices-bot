"""Точка входа Telegram-бота (aiogram 3, long polling)."""
from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.client import ApiClient
from bot.handlers import build_router
from shared.logging_config import setup_logging

logger = logging.getLogger(__name__)


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

    logger.info("Бот запущен (long polling)")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await api.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
