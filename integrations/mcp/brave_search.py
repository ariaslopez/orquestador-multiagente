"""MCP Adaptador — Brave Search.

Reemplaza DuckDuckGo como motor principal de WebScoutAgent.
Brave Search da resultados mas frescos y sin rate-limits agresivos.

Herramientas disponibles:
  search(query, count=5, country='us', search_lang='es')
    -> [{title, url, description, published}]

Env requerida: BRAVE_API_KEY
Docs: https://api.search.brave.com/app/documentation
"""
from __future__ import annotations
import os
import aiohttp
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class BraveSearchAdapter:
    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "search":
            return await self._search(**params)
        raise ValueError(f"BraveSearch: tool '{tool}' desconocida")

    async def _search(
        self,
        query: str,
        count: int = 5,
        country: str = "us",
        search_lang: str = "es",
    ) -> List[Dict]:
        api_key = os.getenv("BRAVE_API_KEY", "")
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        params = {
            "q": query,
            "count": min(count, 20),
            "country": country,
            "search_lang": search_lang,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                BRAVE_ENDPOINT, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title":       item.get("title", ""),
                "url":         item.get("url", ""),
                "description": item.get("description", ""),
                "published":   item.get("page_age", ""),
            })
        logger.debug(f"BraveSearch: '{query}' -> {len(results)} resultados")
        return results


def get_adapter() -> BraveSearchAdapter:
    return BraveSearchAdapter()
