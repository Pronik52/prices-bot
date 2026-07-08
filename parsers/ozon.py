"""Парсер Ozon.

Ozon агрессивно защищён (antibot, капча), поэтому надёжный парсинг требует
headless-браузера / резидентных прокси — это Стадия 2. Пока парсер оформлен
как заглушка: корректно извлекает артикул из ссылки, но при запросе цены
сообщает, что маркетплейс временно не поддерживается.
"""
from __future__ import annotations

import re

from parsers.base import BaseParser, ParseResult
from parsers.exceptions import ParserBlocked
from shared.constants import Marketplace


class OzonParser(BaseParser):
    marketplace = Marketplace.OZON
    # .../product/nazvanie-tovara-123456789/  -> берём последнее число
    url_id_pattern = re.compile(r"product/(?:[\w-]*?-)?(\d+)")

    async def fetch_price(self, external_id: str) -> ParseResult:  # noqa: D401
        raise ParserBlocked(
            "Парсинг Ozon пока не реализован (требуется antibot-обход, Стадия 2)"
        )
