"""
WebScoutAgent — Busca información en la web sobre un activo o tema.

Estrategy:
  1. Si brave_search MCP está disponible → usa MCP (resultados premium)
  2. Fallback → DuckDuckGo via ddgs (sin API key)
  3. Guarda resultado en ctx para que analyst_agent y thesis_agent consuman

Outputs en ctx:
  - ctx.data['web_results']  : lista de {title, body, href}
  - ctx.data['web_sources']  : lista de URLs únicas
  - ctx.data['web_summary']  : resumen de la búsqueda
  - ctx.data['web_provider'] : 'brave_mcp' | 'duckduckgo' | 'none'
"""
from __future__ import annotations
import logging
from core.base_agent import BaseAgent
from core.context import AgentContext

logger = logging.getLogger(__name__)

MAX_RESULTS = 10


class WebScoutAgent(BaseAgent):
    name = "WebScoutAgent"
    description = "Busca y agrega información web actualizada. Soporta brave_search MCP con fallback a DuckDuckGo."

    async def run(self, ctx: AgentContext) -> AgentContext:
        query = ctx.user_input.strip()
        self.log(ctx, f"[WebScout] query: {query[:80]}...")

        results = []
        provider = "none"

        # --- Estrategia 1: brave_search MCP ---
        if ctx.is_mcp_available("brave_search"):
            try:
                raw = await ctx.mcp_call(
                    "brave_search",
                    "brave_web_search",
                    {"query": query, "count": MAX_RESULTS},
                )
                web_results = raw.get("web", {}).get("results", [])
                results = [
                    {
                        "title": r.get("title", ""),
                        "body": r.get("description", ""),
                        "href": r.get("url", ""),
                    }
                    for r in web_results
                ]
                provider = "brave_mcp"
                self.log(ctx, f"[WebScout] brave_search: {len(results)} resultados")
            except Exception as exc:
                logger.warning("[WebScout] brave_search falló: %s — usando fallback", exc)

        # --- Estrategia 2: DuckDuckGo fallback ---
        if not results:
            try:
                from ddgs import DDGS
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=MAX_RESULTS):
                        results.append({
                            "title": r.get("title", ""),
                            "body": r.get("body", ""),
                            "href": r.get("href", ""),
                        })
                provider = "duckduckgo"
                self.log(ctx, f"[WebScout] duckduckgo: {len(results)} resultados")
            except ImportError:
                self.log(ctx, "⚠ ddgs no instalado y brave_search no disponible")
            except Exception as exc:
                self.log(ctx, f"⚠ DuckDuckGo error: {exc}")

        # --- Estructurar outputs ---
        sources = list(dict.fromkeys(r["href"] for r in results if r.get("href")))
        summary = (
            f"{len(results)} resultados vía {provider} para: \"{query[:60]}\""
            if results
            else f"Sin resultados para: \"{query[:60]}\""
        )

        ctx.set_data("web_results", results)
        ctx.set_data("web_sources", sources)
        ctx.set_data("web_summary", summary)
        ctx.set_data("web_provider", provider)

        self.log(ctx, f"[WebScout] ✓ {summary}")
        return ctx
