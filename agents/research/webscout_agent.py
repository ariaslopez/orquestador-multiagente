"""WebScoutAgent — Busca informacion en la web sobre un activo o tema."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class WebScoutAgent(BaseAgent):
    name = "WebScoutAgent"
    description = "Busca y agrega informacion web actualizada sobre el tema de investigacion."

    async def run(self, context: AgentContext) -> AgentContext:
        self.log(context, f"Buscando en web: {context.user_input[:60]}...")
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(context.user_input, max_results=10):
                    results.append({
                        'title': r.get('title', ''),
                        'body': r.get('body', ''),
                        'href': r.get('href', ''),
                    })
            context.web_results = results
            self.log(context, f"Encontrados {len(results)} resultados web")
        except ImportError:
            self.log(context, "⚠ duckduckgo_search no instalado, omitiendo busqueda web")
            context.web_results = []
        except Exception as e:
            self.log(context, f"⚠ Error en busqueda web: {e}")
            context.web_results = []
        return context
