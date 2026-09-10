from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Market:
    symbol: str
    name: str
    market_type: str
    is_otc: bool
    is_open: bool
    payout: float | None


class QuotexMarketProvider:
    """Demo-only market-data adapter.

    Credentials supplied through the dashboard are kept only in process memory.
    The client is always created with is_demo=True. This class never calls buy,
    sell, or other order-execution methods.
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._lock = asyncio.Lock()
        self._cache: list[Market] = []
        self._cache_at: float = 0.0
        self._login: dict[str, str] = {}

    @staticmethod
    def _value(obj: Any, *names: str, default: Any = None) -> Any:
        for name in names:
            if isinstance(obj, dict) and name in obj:
                return obj[name]
            if hasattr(obj, name):
                return getattr(obj, name)
        return default

    def configure(self, *, ssid: str = "", email: str = "", password: str = "") -> None:
        self._login = {}
        if ssid.strip():
            self._login["ssid"] = ssid.strip()
        elif email.strip() and password:
            self._login["email"] = email.strip()
            self._login["password"] = password
        self._cache = []
        self._cache_at = 0.0

    def logged_in(self) -> bool:
        return bool(self._client is not None)

    async def login(self, *, ssid: str = "", email: str = "", password: str = "") -> None:
        self.configure(ssid=ssid, email=email, password=password)
        async with self._lock:
            if self._client is not None:
                return
            client = await self._build_client()
            if client is None:
                raise RuntimeError("Quotex demo client is unavailable or credentials are missing.")
            self._client = client

    async def _build_client(self) -> Any:
        if not self._login:
            return None
        try:
            from QuotexAPI import QuotexAPI  # type: ignore
        except ImportError as exc:
            raise RuntimeError("QuotexAPI package is not installed.") from exc
        kwargs: dict[str, Any] = {"is_demo": True, **self._login}
        client = QuotexAPI(**kwargs)
        result = client.connect()
        if asyncio.iscoroutine(result):
            await result
        return client

    async def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if self._login:
            self._client = await self._build_client()
            return self._client
        if not (os.getenv("QUOTEX_SSID") or (os.getenv("QUOTEX_EMAIL") and os.getenv("QUOTEX_PASSWORD"))):
            return None
        self.configure(
            ssid=os.getenv("QUOTEX_SSID", ""),
            email=os.getenv("QUOTEX_EMAIL", ""),
            password=os.getenv("QUOTEX_PASSWORD", ""),
        )
        self._client = await self._build_client()
        return self._client

    async def get_markets(self, force_refresh: bool = False) -> tuple[list[Market], str]:
        now = asyncio.get_running_loop().time()
        if not force_refresh and now - self._cache_at < 10:
            return self._cache, "cache"

        async with self._lock:
            now = asyncio.get_running_loop().time()
            if not force_refresh and now - self._cache_at < 10:
                return self._cache, "cache"

            client = await self._get_client()
            if client is None:
                return [], "unconfigured"

            raw_assets = await client.get_assets()
            if isinstance(raw_assets, dict):
                items = list(raw_assets.items())
            else:
                items = [(None, item) for item in (raw_assets or [])]

            markets: list[Market] = []
            for key, asset in items:
                symbol = str(self._value(asset, "symbol", "asset", "name", default=key or "UNKNOWN"))
                name = str(self._value(asset, "name", "display_name", default=symbol))
                is_otc = bool(self._value(asset, "is_otc", "otc", default=False)) or symbol.lower().endswith("_otc")
                is_open = bool(self._value(asset, "is_open", "open", "available", default=False))
                asset_type = str(self._value(asset, "type", "asset_type", "category", default="OTHER")).upper()
                payout_value = self._value(asset, "payout", "payout_percent", "profit", default=None)
                try:
                    payout = float(payout_value) if payout_value is not None else None
                except (TypeError, ValueError):
                    payout = None
                markets.append(Market(symbol, name, asset_type, is_otc, is_open, payout))

            self._cache = sorted(markets, key=lambda m: (not m.is_open, m.symbol))
            self._cache_at = asyncio.get_running_loop().time()
            return self._cache, "quotex-demo-api"

    async def logout(self) -> None:
        async with self._lock:
            if self._client is not None:
                disconnect = getattr(self._client, "disconnect", None)
                if disconnect:
                    result = disconnect()
                    if asyncio.iscoroutine(result):
                        await result
            self._client = None
            self._login = {}
            self._cache = []
            self._cache_at = 0.0

    async def close(self) -> None:
        await self.logout()


def market_times() -> dict[str, str]:
    now = datetime.now(timezone.utc)
    ist = now.astimezone(ZoneInfo("Asia/Kolkata"))
    return {
        "server_time": now.isoformat(),
        "server_timezone": "UTC",
        "ist_time": ist.isoformat(),
        "ist_timezone": "Asia/Kolkata",
    }
