"""Хендлеры добавления/просмотра/удаления отслеживаемых товаров."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.client import ApiClient, ApiError
from bot.keyboards import cancel, item_actions, main_menu

router = Router()


class AddItem(StatesGroup):
    waiting_url = State()
    waiting_target = State()


# --- Отмена (работает и во время FSM) ---


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Действие отменено.", reply_markup=main_menu())
    await callback.answer()


# --- Добавление товара ---


@router.callback_query(F.data == "add_item")
async def cb_add_item(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddItem.waiting_url)
    await callback.message.edit_text(
        "Пришли ссылку на товар (Wildberries или Ozon):",
        reply_markup=cancel(),
    )
    await callback.answer()


@router.message(AddItem.waiting_url)
async def on_url(message: Message, state: FSMContext) -> None:
    url = (message.text or "").strip()
    if not url.startswith("http"):
        await message.answer("Это не похоже на ссылку. Пришли URL товара.")
        return
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
        await message.answer(f"⚠️ {exc.detail}", reply_markup=main_menu())
        return

    title = item.get("title") or f"Товар {item['external_id']}"
    goal = f"\nЦель: {target:.0f} ₽" if target is not None else ""
    await message.answer(
        f"✅ Отслеживаю: <b>{title}</b>\n"
        f"Маркетплейс: {item['marketplace']}{goal}",
        reply_markup=main_menu(),
    )


# --- Список и удаление ---


@router.callback_query(F.data == "list_items")
async def cb_list_items(callback: CallbackQuery, api: ApiClient) -> None:
    try:
        items = await api.list_items(callback.from_user.id)
    except ApiError as exc:
        await callback.message.edit_text(f"⚠️ {exc.detail}", reply_markup=main_menu())
        await callback.answer()
        return

    if not items:
        await callback.message.edit_text(
            "У тебя пока нет отслеживаемых товаров.", reply_markup=main_menu()
        )
        await callback.answer()
        return

    await callback.message.edit_text("📋 <b>Твои товары:</b>", reply_markup=main_menu())
    for item in items:
        title = item.get("title") or f"Товар {item['external_id']}"
        last = f"{Decimal(item['last_price']):.0f} ₽" if item.get("last_price") else "—"
        goal = (
            f"\nЦель: {Decimal(item['target_price']):.0f} ₽"
            if item.get("target_price")
            else ""
        )
        text = (
            f"<b>{title}</b>\n"
            f"{item['marketplace']} · текущая цена: {last}{goal}\n"
            f'<a href="{item["url"]}">ссылка</a>'
        )
        await callback.message.answer(text, reply_markup=item_actions(item["id"]))
    await callback.answer()


@router.callback_query(F.data.startswith("del_item:"))
async def cb_delete_item(callback: CallbackQuery, api: ApiClient) -> None:
    item_id = int(callback.data.split(":", 1)[1])
    try:
        await api.delete_item(callback.from_user.id, item_id)
    except ApiError as exc:
        await callback.answer(exc.detail, show_alert=True)
        return
    await callback.message.edit_text("🗑 Товар удалён из отслеживания.")
    await callback.answer()
