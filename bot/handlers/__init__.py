"""Сборка всех роутеров бота."""
from aiogram import Router

from bot.handlers import admin, start, tracking


def build_router() -> Router:
    router = Router()
    router.include_router(admin.router)
    router.include_router(start.router)
    router.include_router(tracking.router)
    # Тарифы/оплата временно отключены (bot.handlers.subscription).
    return router
