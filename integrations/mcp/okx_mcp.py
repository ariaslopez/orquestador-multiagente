"""MCP Adaptador — OKX.

Datos de mercado OKX para el pipeline de trading:
precios spot, futures, funding rates, volumen y orderbook.

Herramientas disponibles:
  get_ticker(instId)               -> {price, 24h_change, volume}
  get_orderbook(instId, sz=20)     -> {bids, asks, timestamp}
  get_candlesticks(instId, bar='1H', limit=100) -> [{ts, open, high, low, close, vol}]
  get_funding_rate(instId)         -> {funding_rate, next_funding_time}
  get_instruments(instType='SPOT') -> [{instId, baseCcy, quoteCcy}]

Env requerida: OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE
Docs: https://www.okx.com/docs-v5
"""
from __future__ import annotations
import os
import aiohttp
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

OKX_BASE = "https://www.okx.com/api/v5"


class OKXMCPAdapter:
    def _headers(self) -> Dict:
        """OKX public endpoints no requieren auth. Privados si."""
        return {"Accept": "application/json"}

    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "get_ticker":        return await self._get_ticker(**params)
        if tool == "get_orderbook":     return await self._get_orderbook(**params)
        if tool == "get_candlesticks":  return await self._get_candlesticks(**params)
        if tool == "get_funding_rate":  return await self._get_funding_rate(**params)
        if tool == "get_instruments":   return await self._get_instruments(**params)
        raise ValueError(f"OKX: tool '{tool}' desconocida")

    async def _get_ticker(self, instId: str) -> Dict:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{OKX_BASE}/market/ticker",
                params={"instId": instId},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        item = data.get("data", [{}])[0]
        return {
            "instId":     item.get("instId"),
            "price":      float(item.get("last", 0)),
            "open24h":    float(item.get("open24h", 0)),
            "high24h":    float(item.get("high24h", 0)),
            "low24h":     float(item.get("low24h", 0)),
            "vol24h":     float(item.get("vol24h", 0)),
            "change_24h": round((float(item.get("last", 0)) - float(item.get("open24h", 1))) /
                                max(float(item.get("open24h", 1)), 0.0001) * 100, 2),
        }

    async def _get_orderbook(self, instId: str, sz: int = 20) -> Dict:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{OKX_BASE}/market/books",
                params={"instId": instId, "sz": sz},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        item = data.get("data", [{}])[0]
        return {"bids": item.get("bids", []), "asks": item.get("asks", []), "ts": item.get("ts")}

    async def _get_candlesticks(self, instId: str, bar: str = "1H", limit: int = 100) -> List[Dict]:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{OKX_BASE}/market/candles",
                params={"instId": instId, "bar": bar, "limit": limit},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        return [
            {"ts": c[0], "open": float(c[1]), "high": float(c[2]),
             "low": float(c[3]), "close": float(c[4]), "vol": float(c[5])}
            for c in data.get("data", [])
        ]

    async def _get_funding_rate(self, instId: str) -> Dict:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{OKX_BASE}/public/funding-rate",
                params={"instId": instId},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        item = data.get("data", [{}])[0]
        return {"funding_rate": item.get("fundingRate"), "next_funding_time": item.get("nextFundingTime")}

    async def _get_instruments(self, instType: str = "SPOT") -> List[Dict]:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{OKX_BASE}/public/instruments",
                params={"instType": instType},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        return [
            {"instId": i["instId"], "baseCcy": i["baseCcy"], "quoteCcy": i["quoteCcy"]}
            for i in data.get("data", [])[:50]
        ]


def get_adapter() -> OKXMCPAdapter:
    return OKXMCPAdapter()
