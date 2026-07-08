"""Точка входа FastAPI-приложения."""
from __future__ import annotations

from fastapi import FastAPI

from api.config import get_settings
from api.routers import items, subscriptions, users
from shared.logging_config import setup_logging

setup_logging(get_settings().log_level)

app = FastAPI(
    title="Price Tracker API",
    version="0.1.0",
    description="Бизнес-логика трекера цен: пользователи, товары, подписки.",
)

app.include_router(users.router)
app.include_router(items.router)
app.include_router(subscriptions.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
