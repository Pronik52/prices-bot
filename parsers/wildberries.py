"""Парсер Wildberries через публичный JSON-эндпоинт карточки товара.

WB отдаёт цены через card.wb.ru без HTML-парсинга — это стабильнее и легче,
чем скрапинг страницы.
"""
from __future__ import annotations

import os
import re
from decimal import ROUND_HALF_UP, Decimal

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from parsers.base import BaseParser, ParseResult
from parsers.exceptions import ItemNotFound, ParserBlocked, PriceUnavailable
from parsers.proxy_manager import proxy_manager
from shared.constants import Marketplace

# WB мигрировал карточку на v4; v2/v1 отдают 404
_CARD_API = "https://card.wb.ru/cards/v4/detail"

# Скидка при оплате WB Кошельком (платформенный промо, ~3%). В ответе API её нет —
# WB применяет её на фронте к цене product. Выносим в env, чтобы менять без кода.
_WALLET_DISCOUNT = Decimal(os.getenv("WB_WALLET_DISCOUNT_PERCENT", "3")) / 100


class WBParser(BaseParser):
    marketplace = Marketplace.WILDBERRIES
    # .../catalog/123456789/detail.aspx  или  ?...nm=123456789
    url_id_pattern = re.compile(r"(?:catalog/|nm=)(\d+)")

    @retry(
        retry=retry_if_exception_type(ParserBlocked),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def fetch_price(
        self, external_id: str, size_id: str | None = None
    ) -> ParseResult:
        params = {
            "appType": "1",
            "curr": "rub",
            "dest": "-1257786",
            "nm": external_id,
        }
        proxy = proxy_manager.get_proxy()
        try:
            async with httpx.AsyncClient(
                timeout=10.0,
                proxy=proxy,
                headers={"User-Agent": "Mozilla/5.0"},
            ) as client:
                resp = await client.get(_CARD_API, params=params)
        except httpx.HTTPError as exc:
            raise ParserBlocked(f"Сетевая ошибка WB: {exc}") from exc

        if resp.status_code == 429:
            raise ParserBlocked("WB вернул 429 (rate limit)")
        if resp.status_code >= 500:
            raise ParserBlocked(f"WB вернул {resp.status_code}")
        if resp.status_code != 200:
            raise ItemNotFound(f"WB вернул статус {resp.status_code}")

        products = self._extract_products(resp.json())
        if not products:
            raise ItemNotFound(f"Товар {external_id} не найден на WB")

        product = products[0]
        title = product.get("name")
        price = self._extract_price(product, size_id)
        if price is None:
            raise PriceUnavailable(f"Цена товара {external_id} недоступна")

        # Цена, которую видит покупатель, — с учётом скидки WB Кошелька
        price = self._apply_wallet_discount(price)

        return ParseResult(
            external_id=external_id,
            price=price,
            title=title,
            in_stock=True,
        )

    @staticmethod
    def _extract_products(body: dict) -> list[dict]:
        """Достаёт список товаров из ответа.

        v4: products на верхнем уровне. v2 и раньше: под ключом data.
        """
        return body.get("products") or (body.get("data") or {}).get("products") or []

    @staticmethod
    def _extract_price(product: dict, size_id: str | None = None) -> Decimal | None:
        """WB отдаёт цену в копейках. Форматы менялись — проверяем варианты.

        v4: sizes[].price.{product,total,basic}; product — цена со скидкой
        продавца (её видит покупатель как основную). Если задан size_id, берём
        цену именно этого варианта (optionId) — у разных размеров цена может
        отличаться. legacy: salePriceU/priceU.
        """
        sizes = product.get("sizes") or []

        # Если указан вариант — сначала пытаемся найти именно его
        if size_id is not None:
            for size in sizes:
                if str(size.get("optionId")) == str(size_id):
                    price = WBParser._price_from_size(size)
                    if price is not None:
                        return price
                    break  # нужный размер найден, но без цены — уходим в общий путь

        # Иначе (или если у выбранного размера нет цены) — первый доступный
        for size in sizes:
            price = WBParser._price_from_size(size)
            if price is not None:
                return price

        # legacy (v2 и раньше): salePriceU / priceU в копейках
        raw = product.get("salePriceU") or product.get("priceU")
        if raw:
            return Decimal(raw) / 100
        return None

    @staticmethod
    def _apply_wallet_discount(price: Decimal) -> Decimal:
        """Применяет скидку WB Кошелька, округляя до целого рубля."""
        discounted = price * (Decimal(1) - _WALLET_DISCOUNT)
        return discounted.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _price_from_size(size: dict) -> Decimal | None:
        price_obj = size.get("price") or {}
        raw = (
            price_obj.get("product")
            or price_obj.get("total")
            or price_obj.get("basic")
        )
        return Decimal(raw) / 100 if raw else None
