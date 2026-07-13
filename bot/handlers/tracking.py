"""Хендлеры добавления/просмотра/удаления отслеживаемых товаров."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, LinkPreviewOptions, Message

from bot.client import ApiClient, ApiError
from bot.keyboards import BTN_ADD, BTN_LIST, cancel, items_list

router = Router()

# Ссылка в сообщении: начинается с http(s), заканчивается на пробеле/переносе/конце.
# ВБ присылает товар текстом «Название\nhttps://...» — вырезаем сам URL.
_URL_RE = re.compile(r"https?://\S+")


class AddItem(StatesGroup):
    waiting_url = State()
    waiting_target = State()


# --- Отмена (работает и во время FSM) ---


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Действие отменено.")
    await callback.answer()


# --- Добавление товара ---
# Кнопки меню — обычные текстовые сообщения. Обработчики без state-фильтра
# зарегистрированы выше FSM-хендлеров, поэтому кнопка меню всегда срабатывает,
# даже если пользователь застрял посреди добавления товара.


@router.message(F.text == BTN_ADD)
async def msg_add_item(message: Message, state: FSMContext) -> None:
    # прерываем возможный процесс добавления — пользователь ушёл в другой пункт меню
    await state.clear()
    await state.set_state(AddItem.waiting_url)
    await message.answer(
        "Пришли ссылку на товар (Wildberries или Ozon):",
        reply_markup=cancel(),
    )


@router.message(F.text == BTN_LIST)
async def msg_list_items(message: Message, state: FSMContext, api: ApiClient) -> None:
    await state.clear()  # см. комментарий в msg_add_item
    try:
        items = await api.list_items(message.from_user.id)
    except ApiError as exc:
        await message.answer(f"⚠️ {exc.detail}")
        return
    await _send_items(message.answer, items)


@router.message(AddItem.waiting_url)
async def on_url(message: Message, state: FSMContext) -> None:
    match = _URL_RE.search(message.text or "")
    if not match:
        await message.answer(
            "Не нашёл ссылку в сообщении. Пришли URL товара (начинается с http)."
        )
        return
    url = match.group(0)
    await state.update_data(url=url)
    await state.set_state(AddItem.waiting_target)
    await message.answer(
        "Укажи целевую цену в рублях (число), "
        "или отправь «-», чтобы просто отслеживать динамику:",
        reply_markup=cancel(),
    )


@router.message(AddItem.waiting_target)
async def on_target(message: Message, state: FSMContext, api: ApiClient) -> None:
    raw = (message.text or "").strip()
    target: Decimal | None = None
    if raw not in {"-", "—", ""}:
        try:
            target = Decimal(raw.replace(",", ".").replace(" ", ""))
            if target <= 0:
                raise InvalidOperation
        except InvalidOperation:
            await message.answer("Не понял цену. Введи число, например 1990, или «-».")
            return

    data = await state.get_data()
    await state.clear()

    try:
        item = await api.add_item(message.from_user.id, data["url"], target)
    except ApiError as exc:
        await message.answer(f"⚠️ {exc.detail}")
        return

    title = item.get("title") or f"Товар {item['external_id']}"
    goal = f"\nЦель: {target:.0f} ₽" if target is not None else ""
    await message.answer(
        f"✅ Отслеживаю: <b>{title}</b>\n"
        f"Маркетплейс: {item['marketplace']}{goal}\n\n"
        f"⏳ Определяю текущую цену — она появится в «Мои товары» через несколько секунд."
    )


# --- Список и удаление ---

_EMPTY_LIST_TEXT = "У тебя пока нет отслеживаемых товаров."


async def _send_items(send, items: list[dict]) -> None:
    """Единый рендер списка через переданный отправитель.

    `send` — это `message.answer` (новое сообщение) или `callback.message.edit_text`
    (правка существующего): оба принимают одинаковые аргументы, поэтому логика
    «пусто / список» живёт в одном месте.
    """
    if not items:
        await send(_EMPTY_LIST_TEXT)
        return
    await send(
        _render_items(items),
        reply_markup=items_list(items),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


def _render_items(items: list[dict]) -> str:
    """Текст списка товаров одним сообщением."""
    lines = ["📋 <b>Твои товары:</b>\n"]
    for i, item in enumerate(items, 1):
        title = item.get("title") or f"Товар {item['external_id']}"
        last = f"{Decimal(item['last_price']):.0f} ₽" if item.get("last_price") else "—"
        goal = (
            f" · цель {Decimal(item['target_price']):.0f} ₽"
            if item.get("target_price")
            else ""
        )
        lines.append(
            f"{i}. <a href=\"{item['url']}\">{title}</a>\n"
            f"   {item['marketplace']} · сейчас {last}{goal}"
        )
    lines.append("\nНажми 🗑, чтобы снять товар с отслеживания.")
    return "\n".join(lines)


@router.callback_query(F.data.startswith("del_item:"))
async def cb_delete_item(callback: CallbackQuery, api: ApiClient) -> None:
    item_id = int(callback.data.split(":", 1)[1])
    try:
        await api.delete_item(callback.from_user.id, item_id)
    except ApiError as exc:
        await callback.answer(exc.detail, show_alert=True)
        return

    # перерисовываем тот же список без удалённого товара
    try:
        items = await api.list_items(callback.from_user.id)
    except ApiError as exc:
        await callback.answer(exc.detail, show_alert=True)
        return

    await _send_items(callback.message.edit_text, items)
    await callback.answer("Удалено")
