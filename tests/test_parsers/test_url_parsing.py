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


def test_wb_price_v4_total_fallback():
    # v4: если нет product, берём total
    product = {"name": "X", "sizes": [{"price": {"total": 149900}}]}
    assert WBParser._extract_price(product) == 1499


def test_wb_price_missing():
    product = {"name": "X", "sizes": [{"price": {}}]}
    assert WBParser._extract_price(product) is None


def test_wb_products_v4_top_level():
    # v4: products на верхнем уровне
    body = {"products": [{"id": 1, "name": "A"}]}
    assert WBParser._extract_products(body)[0]["name"] == "A"


def test_wb_products_legacy_data_wrapper():
    # v2 и раньше: под ключом data
    body = {"data": {"products": [{"id": 2, "name": "B"}]}}
    assert WBParser._extract_products(body)[0]["name"] == "B"


def test_wb_products_empty():
    assert WBParser._extract_products({"products": []}) == []
