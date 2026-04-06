"""WebSearchTool — Búsqueda web usando DuckDuckGo (sin API key)."""
from __future__ import annotations
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class WebSearchTool:
    """
    Realiza búsquedas web usando DuckDuckGo.
    No requiere API key — 100% gratis.
    """

    def __init__(self, max_results: int = 8):
        self.max_results = max_results

    async def search(self, query: str, region: str = "wt-wt") -> List[Dict[str, str]]:
        """
        Busca en la web y retorna lista de resultados.
        Cada resultado: {title, url, snippet}
        """
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, region=region, max_results=self.max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
            logger.info(f"WebSearch: '{query}' → {len(results)} resultados")
            return results
        except Exception as e:
            logger.error(f"WebSearch error: {e}")
            return []

    async def fetch_page(self, url: str) -> str:
        """
        Descarga y extrae el texto de una página web.
        Filtra el ruido HTML y retorna texto limpio.
        """
        try:
            import httpx
            from bs4 import BeautifulSoup
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(response.text, "lxml")
                # Eliminar scripts y estilos
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                # Limpiar líneas vacías múltiples
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                return "\n".join(lines[:300])  # Máx 300 líneas
        except Exception as e:
            logger.error(f"FetchPage error ({url}): {e}")
            return ""

    async def search_and_fetch(self, query: str, top_n: int = 3) -> str:
        """
        Busca y descarga el contenido de los top N resultados.
        Útil para research: obtiene más contexto que solo snippets.
        """
        results = await self.search(query)
        if not results:
            return ""

        content_parts = []
        for r in results[:top_n]:
            content_parts.append(f"## {r['title']}\nFuente: {r['url']}\n")
            page_content = await self.fetch_page(r["url"])
            if page_content:
                content_parts.append(page_content[:2000])  # Máx 2000 chars por página
            content_parts.append("\n---\n")

        return "\n".join(content_parts)
