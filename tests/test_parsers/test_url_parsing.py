"""Тесты разбора ссылок (без сети)."""
from __future__ import annotations

import pytest

from parsers import extract_item_ref
from parsers.exceptions import InvalidUrl, UnsupportedMarketplace
from parsers.wildberries import WBParser
from shared.constants import Marketplace


def test_extract_wb_ref():
    ref = extract_item_ref(
        "https://www.wildberries.ru/catalog/123456789/detail.aspx"
    )
    assert ref.marketplace is Marketplace.WILDBERRIES
    assert ref.external_id == "123456789"


def test_extract_ozon_ref():
    ref = extract_item_ref("https://www.ozon.ru/product/nazvanie-tovara-987654321/")
    assert ref.marketplace is Marketplace.OZON
    assert ref.external_id == "987654321"


def test_unsupported_marketplace():
    with pytest.raises(UnsupportedMarketplace):
        extract_item_ref("https://example.com/product/1")


def test_wb_extract_missing_id():
    with pytest.raises(InvalidUrl):
        extract_item_ref("https://www.wildberries.ru/catalog/detail.aspx")


def test_wb_price_from_sizes():
    product = {"name": "X", "sizes": [{"price": {"product": 199900}}]}
    assert WBParser._extract_price(product) == 1999


def test_wb_price_legacy():
    product = {"name": "X", "salePriceU": 250000}
    assert WBParser._extract_price(product) == 2500
