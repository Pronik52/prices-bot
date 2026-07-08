"""Абстрактный интерфейс парсера маркетплейса.

Добавление нового маркетплейса = новый наследник BaseParser. Ядро системы
(воркеры, планировщик) работает только через этот интерфейс.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from shared.constants import Marketplace


@dataclass(frozen=True)
class ItemRef:
    """Ссылка на товар, разобранная из URL."""

    marketplace: Marketplace
    external_id: str


@dataclass(frozen=True)
class ParseResult:
    """Результат парсинга одного товара."""

    external_id: str
    price: Decimal
    title: str | None = None
    in_stock: bool = True


class BaseParser(ABC):
    """Базовый класс парсера. Один наследник = один маркетплейс."""

    marketplace: Marketplace
    # regex для извлечения артикула из URL; заполняется наследником
    url_id_pattern: re.Pattern[str]

    @classmethod
    def extract_external_id(cls, url: str) -> str:
        """Извлекает артикул товара из ссылки. Бросает ValueError, если не найден."""
        match = cls.url_id_pattern.search(url)
        if not match:
            raise ValueError(f"Не удалось извлечь артикул из ссылки: {url}")
        return match.group(1)

    @abstractmethod
    async def fetch_price(self, external_id: str) -> ParseResult:
        """Возвращает актуальную цену товара по его артикулу.

        Должен бросать соответствующие исключения из parsers.exceptions:
        ItemNotFound, ParserBlocked, PriceUnavailable.
        """
        raise NotImplementedError
