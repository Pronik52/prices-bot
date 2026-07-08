"""HTTP-клиент к API-сервису. Бот не ходит в БД напрямую — только через API."""
from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

import httpx


class ApiError(Exception):
    """Ошибка ответа API. Содержит человекочитаемое сообщение (detail)."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class ApiClient:
    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("API_BASE_URL", "http://api:8000")).rstrip("/")
        self.token = token or os.getenv("INTERNAL_API_TOKEN", "dev-internal-token")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-Internal-Token": self.token},
            timeout=15.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        resp = await self._client.request(method, path, **kwargs)
        if resp.status_code >= 400:
            detail = "Ошибка сервиса"
            try:
                detail = resp.json().get("detail", detail)
            except Exception:  # noqa: BLE001
                pass
            raise ApiError(resp.status_code, detail)
        return resp

    # --- Пользователи ---

    async def register_user(self, telegram_id: int, username: str | None) -> dict:
        resp = await self._request(
            "POST", "/users", json={"telegram_id": telegram_id, "username": username}
        )
        return resp.json()

    # --- Товары ---

    async def add_item(
        self, telegram_id: int, url: str, target_price: Decimal | None
    ) -> dict:
        payload: dict[str, Any] = {"telegram_id": telegram_id, "url": url}
        if target_price is not None:
            payload["target_price"] = str(target_price)
        resp = await self._request("POST", "/items", json=payload)
        return resp.json()

    async def list_items(self, telegram_id: int) -> list[dict]:
        resp = await self._request(
            "GET", "/items", params={"telegram_id": telegram_id}
        )
        return resp.json()

    async def delete_item(self, telegram_id: int, item_id: int) -> None:
        await self._request(
            "DELETE", f"/items/{item_id}", params={"telegram_id": telegram_id}
        )

    # --- Подписки ---

    async def list_tiers(self) -> dict[str, int]:
        resp = await self._request("GET", "/subscriptions/tiers")
        return resp.json()
