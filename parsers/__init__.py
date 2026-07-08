"""Публичный интерфейс слоя парсеров: реестр и разбор ссылок."""
from __future__ import annotations

from parsers.base import BaseParser, ItemRef, ParseResult
from parsers.exceptions import InvalidUrl, UnsupportedMarketplace
from parsers.ozon import OzonParser
from parsers.wildberries import WBParser
from shared.constants import Marketplace, marketplace_from_url

# Реестр парсеров по маркетплейсу
PARSER_REGISTRY: dict[Marketplace, type[BaseParser]] = {
    Marketplace.WILDBERRIES: WBParser,
    Marketplace.OZON: OzonParser,
}


def get_parser(marketplace: Marketplace) -> BaseParser:
    """Возвращает экземпляр парсера для маркетплейса."""
    parser_cls = PARSER_REGISTRY.get(marketplace)
    if parser_cls is None:
        raise UnsupportedMarketplace(f"Нет парсера для {marketplace}")
    return parser_cls()


def extract_item_ref(url: str) -> ItemRef:
    """Определяет маркетплейс и артикул по ссылке (без сетевых запросов)."""
    marketplace = marketplace_from_url(url)
    if marketplace is None:
        raise UnsupportedMarketplace("Ссылка не относится к поддерживаемым маркетплейсам")
    parser_cls = PARSER_REGISTRY[marketplace]
    try:
        external_id = parser_cls.extract_external_id(url)
    except ValueError as exc:
        raise InvalidUrl(str(exc)) from exc
    return ItemRef(marketplace=marketplace, external_id=external_id)


__all__ = [
    "BaseParser",
    "ItemRef",
    "ParseResult",
    "PARSER_REGISTRY",
    "get_parser",
    "extract_item_ref",
]
