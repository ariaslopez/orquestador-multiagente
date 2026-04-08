"""ResponseAgent — Consolida y formatea la respuesta final al usuario.

Migrado de agents/response_agent.py (v1) a agents/shared/ en PR-2.
Este agente es TRANSVERSAL: puede ser la última etapa de cualquier pipeline
como paso de formateo/presentación opcional.

Adaptaciones:
  - BaseAgent v2: run(ctx: AgentContext) async
  - ctx.user_input en lugar de context.user_query
  - ctx.final_output en lugar de context.final_response
  - Lee ctx.data para construir la respuesta (no accede a atributos v1)
  - api_router integrado para modo LLM (reemplaza ollama directo)

Estrategia:
  1. Si hay final_output ya seteado → solo aplica formato limpio
  2. Si hay ctx.data con resultados → sintetiza con LLM (api_router)
  3. Fallback → respuesta estructurada de plantilla
"""
from __future__ import annotations
import logging
from core.base_agent import BaseAgent
from core.context import AgentContext

logger = logging.getLogger(__name__)


class ResponseAgent(BaseAgent):
    """Etapa final opcional: consolida y formatea el output del pipeline."""

    name        = "ResponseAgent"
    description = "Consolida outputs del pipeline y genera la respuesta final al usuario."

    async def run(self, ctx: AgentContext) -> AgentContext:
        # Si ya hay un final_output definido por otro agente, solo limpiamos
        if ctx.final_output and len(ctx.final_output.strip()) > 50:
            self.log(ctx, "[ResponseAgent] final_output ya presente — aplicando formato")
            ctx.final_output = self._format_output(ctx.final_output)
            return ctx

        # Intentar sintetizar con LLM via api_router
        try:
            ctx = await self._synthesize_with_llm(ctx)
        except Exception as exc:
            logger.warning("[ResponseAgent] LLM synthesis falló: %s — usando template", exc)
            ctx.final_output = self._build_template_response(ctx)

        return ctx

    async def _synthesize_with_llm(self, ctx: AgentContext) -> AgentContext:
        """Sintetiza el output usando el api_router (Ollama/Groq/Gemini)."""
        from core.api_router import APIRouter
        router = APIRouter()

        # Recopilar datos relevantes del contexto
        data_summary = []
        for key, value in ctx.data.items():
            if value and key not in ("memory_context",):
                data_summary.append(f"- {key}: {str(value)[:300]}")

        data_str = "\n".join(data_summary) if data_summary else "(sin datos de agentes)"

        prompt = (
            f"Sintetiza los siguientes resultados del pipeline en una respuesta clara "
            f"y accionable para el usuario.\n\n"
            f"Tarea original: {ctx.user_input}\n\n"
            f"Datos del pipeline:\n{data_str}\n\n"
            f"Genera una respuesta en el mismo idioma de la tarea. "
            f"Sé conciso, directo y orientado a la acción."
        )

        response, tokens = await router.complete(
            messages=[{"role": "user", "content": prompt}],
            task_type="synthesis",
            temperature=0.3,
            max_tokens=800,
        )
        ctx.final_output = self._format_output(response)
        ctx.add_tokens(tokens, api="api_router")
        self.log(ctx, f"[ResponseAgent] respuesta sintetizada ({tokens} tokens)")
        return ctx

    def _build_template_response(self, ctx: AgentContext) -> str:
        """Fallback de plantilla si el LLM falla."""
        parts = [
            f"\U0001f4cb **Tarea:** {ctx.user_input}",
            f"\U0001f9e9 **Pipeline:** {ctx.task_type}",
            "",
        ]
        for key, value in ctx.data.items():
            if value and key not in ("memory_context",):
                parts.append(f"**{key}:**")
                parts.append(f"{str(value)[:500]}")
                parts.append("")

        if ctx.failed_agents:
            parts.append(f"\u26a0\ufe0f Agentes con errores: {', '.join(ctx.failed_agents)}")

        return "\n".join(parts)

    @staticmethod
    def _format_output(text: str) -> str:
        """Limpia whitespace extra y asegura un final limpio."""
        return text.strip()
