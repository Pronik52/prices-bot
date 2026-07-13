"""Админка: сводка и постраничный список пользователей.

Доступ ограничен списком Telegram-ID из ADMIN_TELEGRAM_IDS. Не-админам команда
`/admin` и админские callback'и не отвечают вовсе (фильтр отсекает их до хендлера),
поэтому панель невидима для обычных пользователей. Если список пуст — админка
выключена целиком.
"""
from __future__ import annotations

import html
import logging
import os

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.client import ApiClient, ApiError

logger = logging.getLogger(__name__)

# Должно совпадать с page_size по умолчанию в API (api.services.admin_service):
# используется только для сквозной нумерации строк между страницами.
USERS_PER_PAGE = 10


def _parse_admin_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            logger.warning("ADMIN_TELEGRAM_IDS: не число, пропускаю: %r", part)
    return ids


ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_TELEGRAM_IDS", ""))

# Отдельный роутер, чьи апдейты пропускаются только от админов.
router = Router()
router.message.filter(F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))


def _plural_items(n: int) -> str:
    """Правильная форма слова «товар» для числа n."""
    if n % 100 in (11, 12, 13, 14):
        return "товаров"
    last = n % 10
    if last == 1:
        return "товар"
    if last in (2, 3, 4):
        return "товара"
    return "товаров"


# --- Рендер экранов ---


def _render_dashboard(stats: dict):
    text = (
        "📊 <b>Админка</b>\n\n"
        f"👤 Пользователей: <b>{stats['total_users']}</b>\n"
        f"📦 Товаров отслеживается: <b>{stats['total_items']}</b>\n"
        f"✅ Активных товаров: <b>{stats['active_items']}</b>\n"
        f"🆕 Новых за 7 дней: <b>{stats['new_users_7d']}</b>"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Пользователи", callback_data="adm:users:1")
    builder.button(text="🔄 Обновить", callback_data="adm:home")
    builder.adjust(1)
    return text, builder.as_markup()


def _render_users(data: dict):
    total = data["total_users"]
    page = data["page"]
    total_pages = data["total_pages"]
    users = data["users"]

    if total == 0:
        text = "👥 <b>Пользователи</b>\n\nПока никто не зарегистрировался."
    else:
        lines = [f"👥 <b>Пользователи</b> — всего {total}\n"]
        base = (page - 1) * USERS_PER_PAGE
        for offset, u in enumerate(users, start=1):
            if u["username"]:
                ident = f"@{html.escape(u['username'])}"
            else:
                ident = f"id {u['telegram_id']}"
            count = u["item_count"]
            lines.append(f"{base + offset}. {ident} · {count} {_plural_items(count)}")
        lines.append(f"\nСтраница {page} / {total_pages}")
        text = "\n".join(lines)

    builder = InlineKeyboardBuilder()
    nav: list[InlineKeyboardButton] = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"adm:users:{page - 1}")
        )
    if total_pages > 1:
        nav.append(
            InlineKeyboardButton(
                text=f"{page}/{total_pages}", callback_data="adm:noop"
            )
        )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"adm:users:{page + 1}")
        )
    if nav:
        builder.row(*nav)
    builder.row(
        InlineKeyboardButton(text="◀️ В админку", callback_data="adm:home")
    )
    return text, builder.as_markup()


async def _safe_edit(callback: CallbackQuery, text: str, markup) -> None:
    """Правит сообщение, гася «message is not modified» (например при «Обновить»
    без реальных изменений) — иначе aiogram кинет исключение на повторе."""
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise


# --- Хендлеры ---


@router.message(Command("admin"))
async def cmd_admin(message: Message, api: ApiClient) -> None:
    try:
        stats = await api.get_admin_stats()
    except ApiError as exc:
        await message.answer(f"⚠️ {exc.detail}")
        return
    text, markup = _render_dashboard(stats)
    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data == "adm:home")
async def cb_admin_home(callback: CallbackQuery, api: ApiClient) -> None:
    try:
        stats = await api.get_admin_stats()
    except ApiError as exc:
        await callback.answer(exc.detail, show_alert=True)
        return
    text, markup = _render_dashboard(stats)
    await _safe_edit(callback, text, markup)
    await callback.answer()


@router.callback_query(F.data.startswith("adm:users:"))
async def cb_admin_users(callback: CallbackQuery, api: ApiClient) -> None:
    page = int(callback.data.rsplit(":", 1)[1])
    try:
        data = await api.get_admin_users(page)
    except ApiError as exc:
        await callback.answer(exc.detail, show_alert=True)
        return
    text, markup = _render_users(data)
    await _safe_edit(callback, text, markup)
    await callback.answer()


@router.callback_query(F.data == "adm:noop")
async def cb_admin_noop(callback: CallbackQuery) -> None:
    # индикатор страницы — просто гасим «часики»
    await callback.answer()
