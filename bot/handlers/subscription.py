"""Хендлеры показа тарифов. Реальная оплата — Стадия 2."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.client import ApiClient, ApiError
from bot.keyboards import main_menu

router = Router()

_TIER_TITLES = {"free": "🆓 Free", "premium": "💎 Premium"}


@router.callback_query(F.data == "show_tiers")
async def cb_show_tiers(callback: CallbackQuery, api: ApiClient) -> None:
    try:
        tiers = await api.list_tiers()
    except ApiError as exc:
        await callback.message.edit_text(f"⚠️ {exc.detail}", reply_markup=main_menu())
        await callback.answer()
        return

    lines = ["💎 <b>Тарифы</b>\n"]
    for tier, limit in tiers.items():
        title = _TIER_TITLES.get(tier, tier)
        lines.append(f"{title} — до {limit} товаров")
    lines.append("\nОплата появится в ближайшее время.")

    await callback.message.edit_text("\n".join(lines), reply_markup=main_menu())
    await callback.answer()
