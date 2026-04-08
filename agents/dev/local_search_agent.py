"""LocalSearchAgent — Busca documentación en la base de conocimiento local.

Migrado de agents/search_agent.py (v1) a agents/dev/ en PR-2.
Renombrado a LocalSearchAgent para evitar colisión con:
  - agents/research/webscout_agent.py (búsqueda web via brave_search MCP)

Rol: fallback de documentación offline. Útil cuando MCPs no están
disponibles o para consultar docs internas del proyecto.

Adaptaciones:
  - BaseAgent v2: run(ctx: AgentContext) async
  - ctx.user_input en lugar de context.user_query
  - ctx.set_data() en lugar de context.search_results
  - Lee ctx.data['detected_language'] si LanguageAgent corrió antes
"""
from __future__ import annotations
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent / "knowledge_base" / "docs"


class LocalSearchAgent(BaseAgent):
    """Busca archivos .md en knowledge_base/docs/ relevantes para la tarea."""

    name        = "LocalSearchAgent"
    description = "Busca documentación local relevante. Fallback offline cuando MCPs no están disponibles."

    async def run(self, ctx: AgentContext) -> AgentContext:
        lang         = ctx.get_data("detected_language", "general")
        query_words  = set(ctx.user_input.lower().split())
        results: list[dict] = []

        search_path = KNOWLEDGE_BASE_PATH / lang
        if not search_path.exists():
            search_path = KNOWLEDGE_BASE_PATH

        if not search_path.exists():
            self.log(ctx, f"[LocalSearchAgent] knowledge_base no encontrada en {search_path}")
            ctx.set_data("local_docs", [])
            return ctx

        for file_path in search_path.rglob("*.md"):
            try:
                content     = file_path.read_text(encoding="utf-8")
                content_words = set(content.lower().split())
                score       = len(query_words & content_words)
                if score > 0:
                    results.append({
                        "file":    str(file_path),
                        "score":   score,
                        "preview": content[:300],
                        "content": content,
                        "source":  str(file_path),
                    })
            except Exception:
                continue

        results.sort(key=lambda x: x["score"], reverse=True)
        top = results[:5]
        ctx.set_data("local_docs", top)
        self.log(ctx, f"[LocalSearchAgent] {len(top)} docs encontrados para '{lang}'")
        return ctx
