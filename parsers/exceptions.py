"""Исключения слоя парсинга."""
from __future__ import annotations


class ParserError(Exception):
    """Базовое исключение парсеров."""


class InvalidUrl(ParserError):
    """Ссылка не распознана / не содержит артикула."""


class UnsupportedMarketplace(ParserError):
    """Домен ссылки не относится к поддерживаемым маркетплейсам."""


class ItemNotFound(ParserError):
    """Товар не найден на маркетплейсе (удалён/недоступен)."""


class ParserBlocked(ParserError):
    """Маркетплейс заблокировал запрос (капча/бан/429). Кандидат на retry с прокси."""


class PriceUnavailable(ParserError):
    """Товар найден, но цена недоступна (нет в наличии и т.п.)."""
