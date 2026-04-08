"""MCP Adaptador — CoinGecko.

Datos de mercado crypto en tiempo real para el pipeline trading.
Utiliza la API publica de CoinGecko (no requiere key para uso basico)
y la Pro API si COINGECKO_API_KEY esta configurada.

Herramientas disponibles:
  get_price(ids, vs_currencies='usd')          -> {bitcoin: {usd: 95000}}
  get_market_data(id, days=7)                  -> {prices, volumes, market_caps}
  get_trending()                               -> [{coin, rank, price_change_24h}]
  get_coin_info(id)                            -> {name, description, links, ...}
  search(query)                               -> [{id, name, symbol}]

Env opcional: COINGECKO_API_KEY (para mas requests/min)
"""
from __future__ import annotations
import os
import aiohttp
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

BASE_URL = "https://api.coingecko.com/api/v3"
PRO_URL  = "https://pro-api.coingecko.com/api/v3"


class CoinGeckoMCPAdapter:
    def _get_base(self) -> str:
        key = os.getenv("COINGECKO_API_KEY", "")
        return PRO_URL if key else BASE_URL

    def _headers(self) -> Dict:
        key = os.getenv("COINGECKO_API_KEY", "")
        return {"x-cg-pro-api-key": key} if key else {}

    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "get_price":       return await self._get_price(**params)
        if tool == "get_market_data": return await self._get_market_data(**params)
        if tool == "get_trending":    return await self._get_trending()
        if tool == "get_coin_info":   return await self._get_coin_info(**params)
        if tool == "search":          return await self._search(**params)
        raise ValueError(f"CoinGecko: tool '{tool}' desconocida")

    async def _get_price(self, ids: str, vs_currencies: str = "usd") -> Dict:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{self._get_base()}/simple/price",
                params={"ids": ids, "vs_currencies": vs_currencies,
                        "include_24hr_change": "true", "include_market_cap": "true"},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        logger.debug(f"CoinGecko: precio obtenido para {ids}")
        return data

    async def _get_market_data(self, id: str, days: int = 7) -> Dict:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{self._get_base()}/coins/{id}/market_chart",
                params={"vs_currency": "usd", "days": days},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                return await r.json()

    async def _get_trending(self) -> List[Dict]:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{self._get_base()}/search/trending",
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        coins = data.get("coins", [])
        return [
            {
                "id":              c["item"]["id"],
                "name":            c["item"]["name"],
                "symbol":          c["item"]["symbol"],
                "market_cap_rank": c["item"].get("market_cap_rank"),
                "price_btc":       c["item"].get("price_btc"),
            }
            for c in coins[:10]
        ]

    async def _get_coin_info(self, id: str) -> Dict:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{self._get_base()}/coins/{id}",
                params={"localization": "false", "tickers": "false",
                        "community_data": "false", "developer_data": "false"},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                r.raise_for_status()
                return await r.json()

    async def _search(self, query: str) -> List[Dict]:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{self._get_base()}/search",
                params={"query": query},
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                r.raise_for_status()
                data = await r.json()
        return [{"id": c["id"], "name": c["name"], "symbol": c["symbol"]} for c in data.get("coins", [])[:10]]


def get_adapter() -> CoinGeckoMCPAdapter:
    return CoinGeckoMCPAdapter()
