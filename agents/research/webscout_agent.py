"""
WebScoutAgent v2 — Investigación web de producción.

Estrategia de búsqueda en cascada (fallback automático):
  1. brave_search   → resultados frescos con API key (premium)
  2. deepwiki       → conocimiento técnico/wiki estructurado
  3. playwright_mcp → scraping directo si las dos anteriores fallan
  4. DuckDuckGo     → último recurso, sin API key

Descomposición inteligente de queries:
  - Si la query supera COMPLEX_QUERY_THRESHOLD palabras, llama a
    sequential_thinking.decompose() para obtener sub-queries
    especializadas, ejecutarlas en paralelo y fusionar resultados.
  - Para queries simples (≤ umbral) va directo al buscador.

Memoria episódica:
  - _before_run(): recuperada automáticamente por BaseAgent.execute()
    (key = "research:WebScoutAgent:last")
  - _after_run():  BaseAgent guarda el output si ctx.data contiene
    "webscoutagent_output" (clave estandarizada).
  - Además, WebScoutAgent enriquece esa clave con el resumen final
    para que _after_run() tenga algo útil que persistir.

Outputs en ctx.data:
  web_results   : List[{title, url, description, published}]
  web_sources   : List[str]  — URLs únicas deduplicadas
  web_summary   : str        — resumen legible del scouting
  web_provider  : str        — 'brave' | 'deepwiki' | 'playwright' | 'duckduckgo' | 'none'
  web_queries   : List[str]  — queries reales ejecutadas
  webscoutagent_output : str — clave estandarizada para _after_run() de BaseAgent

Pipeline consumers:
  AnalystAgent y ThesisAgent leen ctx.data['web_results'] y
  ctx.data['web_sources'] para construir sus análisis.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from core.base_agent import BaseAgent
from core.context import AgentContext

logger = logging.getLogger(__name__)

# Umbral de palabras para activar descomposición con sequential_thinking
COMPLEX_QUERY_THRESHOLD = 8
MAX_RESULTS_PER_SOURCE  = 10
MAX_PARALLEL_QUERIES    = 5   # límite para asyncio.gather en sub-queries


# ---------------------------------------------------------------------------
# Tipos internos
# ---------------------------------------------------------------------------

WebResult = Dict[str, str]   # {title, url, description, published}


class WebScoutAgent(BaseAgent):
    """
    Agente de scouting web con búsqueda en cascada, descomposición
    inteligente de queries y memoria episódica automática.
    """

    name        = "WebScoutAgent"
    description = (
        "Investiga cualquier tema en la web usando múltiples fuentes "
        "(Brave, DeepWiki, Playwright, DuckDuckGo). "
        "Descompone queries complejas con sequential_thinking y "
        "consolida resultados en un output estructurado para el pipeline."
    )

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------

    async def run(self, ctx: AgentContext) -> AgentContext:
        query = ctx.user_input.strip()
        self.log(ctx, f"🔍 Iniciando scouting: «{query[:80]}»")

        # Determinar si la query es lo suficientemente compleja para
        # justificar descomposición con sequential_thinking
        queries_to_run: List[str] = await self._plan_queries(ctx, query)

        # Ejecutar todas las queries en paralelo (limitado a MAX_PARALLEL_QUERIES)
        all_results: List[WebResult] = []
        provider_used = "none"

        search_tasks = [
            self._search_single(ctx, q)
            for q in queries_to_run[:MAX_PARALLEL_QUERIES]
        ]
        batch_results: List[Tuple[List[WebResult], str]] = await asyncio.gather(
            *search_tasks, return_exceptions=False
        )

        for results, provider in batch_results:
            all_results.extend(results)
            if provider != "none":
                provider_used = provider   # registra el último provider activo

        # Deduplicar por URL manteniendo orden de aparición
        seen_urls: set = set()
        unique_results: List[WebResult] = []
        for r in all_results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)

        sources = [r["url"] for r in unique_results if r.get("url")]

        summary = self._build_summary(query, unique_results, provider_used, queries_to_run)

        # --- Escribir outputs en ctx ---
        ctx.set_data("web_results",  unique_results)
        ctx.set_data("web_sources",  sources)
        ctx.set_data("web_summary",  summary)
        ctx.set_data("web_provider", provider_used)
        ctx.set_data("web_queries",  queries_to_run)

        # Clave estandarizada para BaseAgent._after_run() → memoria episódica
        ctx.set_data("webscoutagent_output", summary)

        self.log(ctx, f"✅ {summary}")
        return ctx

    # ------------------------------------------------------------------
    # Planificación de queries
    # ------------------------------------------------------------------

    async def _plan_queries(self, ctx: AgentContext, query: str) -> List[str]:
        """
        Decide si la query se ejecuta directamente o se descompone.

        Para queries complejas (> COMPLEX_QUERY_THRESHOLD palabras),
        invoca sequential_thinking.decompose() para obtener sub-queries
        especializadas. Si el MCP no está disponible o falla, vuelve
        a la query original.
        """
        word_count = len(query.split())
        if word_count <= COMPLEX_QUERY_THRESHOLD:
            return [query]

        if not ctx.is_mcp_available("sequential_thinking"):
            self.log(ctx, "sequential_thinking no disponible — query simple")
            return [query]

        try:
            decomposition = await ctx.mcp_call(
                "sequential_thinking",
                "decompose",
                {"task": f"Buscar información web sobre: {query}", "max_subtasks": 4},
            )
            subtasks = decomposition.get("subtasks", [])
            sub_queries = [
                s.get("description", "").replace("Buscar: ", "").replace("Investigar: ", "").strip()
                for s in subtasks
                if s.get("description")
            ]
            if sub_queries:
                self.log(ctx, f"🧠 Query descompuesta en {len(sub_queries)} sub-queries")
                return sub_queries
        except Exception as exc:
            logger.warning("[WebScout] sequential_thinking.decompose falló: %s", exc)

        return [query]

    # ------------------------------------------------------------------
    # Búsqueda individual (cascade)
    # ------------------------------------------------------------------

    async def _search_single(
        self, ctx: AgentContext, query: str
    ) -> Tuple[List[WebResult], str]:
        """
        Ejecuta la búsqueda para una query siguiendo la cascada de providers.
        Retorna (results, provider_name).
        """
        # 1. Brave Search
        results, provider = await self._try_brave(ctx, query)
        if results:
            return results, provider

        # 2. DeepWiki (conocimiento técnico/estructurado)
        results, provider = await self._try_deepwiki(ctx, query)
        if results:
            return results, provider

        # 3. Playwright MCP (scraping directo)
        results, provider = await self._try_playwright(ctx, query)
        if results:
            return results, provider

        # 4. DuckDuckGo (último recurso)
        results, provider = await self._try_duckduckgo(query)
        if results:
            return results, provider

        self.log(ctx, f"⚠ Sin resultados para: «{query[:60]}»")
        return [], "none"

    # ------------------------------------------------------------------
    # Providers
    # ------------------------------------------------------------------

    async def _try_brave(
        self, ctx: AgentContext, query: str
    ) -> Tuple[List[WebResult], str]:
        if not ctx.is_mcp_available("brave_search"):
            return [], "none"
        try:
            raw: List[Dict] = await ctx.mcp_call(
                "brave_search",
                "search",
                {"query": query, "count": MAX_RESULTS_PER_SOURCE},
            )
            results = [
                {
                    "title":       r.get("title", ""),
                    "url":         r.get("url", ""),
                    "description": r.get("description", ""),
                    "published":   r.get("published", ""),
                }
                for r in (raw or [])
                if r.get("url")
            ]
            if results:
                logger.debug("[WebScout] brave_search: %d resultados para «%s»", len(results), query[:40])
                return results, "brave"
        except Exception as exc:
            logger.warning("[WebScout] brave_search falló: %s — intentando siguiente provider", exc)
        return [], "none"

    async def _try_deepwiki(
        self, ctx: AgentContext, query: str
    ) -> Tuple[List[WebResult], str]:
        if not ctx.is_mcp_available("deepwiki"):
            return [], "none"
        try:
            raw = await ctx.mcp_call(
                "deepwiki",
                "search",
                {"query": query, "max_results": MAX_RESULTS_PER_SOURCE},
            )
            entries = raw if isinstance(raw, list) else raw.get("results", [])
            results = [
                {
                    "title":       e.get("title", ""),
                    "url":         e.get("url", e.get("source", "")),
                    "description": e.get("summary", e.get("content", ""))[:300],
                    "published":   "",
                }
                for e in (entries or [])
                if e.get("url") or e.get("source")
            ]
            if results:
                logger.debug("[WebScout] deepwiki: %d resultados para «%s»", len(results), query[:40])
                return results, "deepwiki"
        except Exception as exc:
            logger.warning("[WebScout] deepwiki falló: %s", exc)
        return [], "none"

    async def _try_playwright(
        self, ctx: AgentContext, query: str
    ) -> Tuple[List[WebResult], str]:
        """
        Usa playwright_mcp para hacer una búsqueda web directa.
        Navega a DuckDuckGo HTML y extrae los resultados del DOM.
        """
        if not ctx.is_mcp_available("playwright_mcp"):
            return [], "none"
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            raw = await ctx.mcp_call(
                "playwright_mcp",
                "navigate_and_extract",
                {
                    "url":      ddg_url,
                    "selector": ".result__body",
                    "limit":    MAX_RESULTS_PER_SOURCE,
                },
            )
            items = raw if isinstance(raw, list) else raw.get("items", [])
            results = [
                {
                    "title":       item.get("title", ""),
                    "url":         item.get("url", item.get("href", "")),
                    "description": item.get("text", item.get("description", ""))[:300],
                    "published":   "",
                }
                for item in (items or [])
                if item.get("url") or item.get("href")
            ]
            if results:
                logger.debug("[WebScout] playwright: %d resultados", len(results))
                return results, "playwright"
        except Exception as exc:
            logger.warning("[WebScout] playwright_mcp falló: %s", exc)
        return [], "none"

    async def _try_duckduckgo(
        self, query: str
    ) -> Tuple[List[WebResult], str]:
        try:
            from ddgs import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=MAX_RESULTS_PER_SOURCE):
                    results.append({
                        "title":       r.get("title", ""),
                        "url":         r.get("href", ""),
                        "description": r.get("body", ""),
                        "published":   "",
                    })
            if results:
                logger.debug("[WebScout] duckduckgo: %d resultados", len(results))
                return results, "duckduckgo"
        except ImportError:
            logger.warning("[WebScout] ddgs no instalado")
        except Exception as exc:
            logger.warning("[WebScout] DuckDuckGo error: %s", exc)
        return [], "none"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_summary(
        self,
        original_query: str,
        results: List[WebResult],
        provider: str,
        queries: List[str],
    ) -> str:
        multi = len(queries) > 1
        query_info = (
            f"{len(queries)} sub-queries ejecutadas"
            if multi
            else f"«{original_query[:60]}»"
        )
        if results:
            return (
                f"{len(results)} resultados únicos vía {provider} — {query_info}"
            )
        return f"Sin resultados para {query_info}"
