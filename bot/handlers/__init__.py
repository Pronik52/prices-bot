"""Сборка всех роутеров бота."""
from aiogram import Router

from bot.handlers import start, subscription, tracking


def build_router() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(tracking.router)
    router.include_router(subscription.router)
    return router
