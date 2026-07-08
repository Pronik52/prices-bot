"""Ротация прокси для парсеров.

На Стадии 1 — простой round-robin по списку из env PROXY_LIST. Если список пуст,
запросы идут напрямую. Retry-логика реализована в самих парсерах через tenacity.
"""
from __future__ import annotations

import itertools
import os
import threading


class ProxyManager:
    def __init__(self, proxies: list[str] | None = None) -> None:
        if proxies is None:
            raw = os.getenv("PROXY_LIST", "")
            proxies = [p.strip() for p in raw.split(",") if p.strip()]
        self._proxies = proxies
        self._lock = threading.Lock()
        self._cycle = itertools.cycle(proxies) if proxies else None

    @property
    def enabled(self) -> bool:
        return self._cycle is not None

    def get_proxy(self) -> str | None:
        """Следующий прокси по кругу или None, если прокси не настроены."""
        if self._cycle is None:
            return None
        with self._lock:
            return next(self._cycle)


# Глобальный экземпляр — переиспользуется воркерами
proxy_manager = ProxyManager()
