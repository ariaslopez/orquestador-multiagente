"""SchedulerAgent — propone timing de publicacion y genera variantes para A/B testing."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class SchedulerAgent(BaseAgent):
    name = "SchedulerAgent"
    description = "Propone horario optimo de publicacion y genera variantes para A/B testing."

    async def run(self, context: AgentContext) -> AgentContext:
        final_content = context.get_data('content_final') or context.get_data('content_edited') or ''
        brief_data = context.get_data('content_brief') or {}
        content_type = brief_data.get('content_type', 'thread')

        self.log(context, "Generando schedule y variantes...")

        prompt = f"""Eres un social media strategist especializado en contenido crypto.

CONTENIDO FINAL:
{final_content[:2000]}

TIPO: {content_type}

Genera:

## TIMING OPTIMO DE PUBLICACION
- Mejor dia de la semana y por que
- Mejor hora (UTC y America/Bogota)
- Ventana de mayor engagement para audiencia crypto

## VARIANTE A (original)
{final_content[:500]}...

## VARIANTE B (hook alternativo)
(Reescribe solo los primeros 1-2 tweets/parrafos con un angulo diferente)

## METRICAS A TRACKEAR
- KPIs especificos para este contenido
- Que considera 'exito' en 24h y en 7 dias

## CONTENIDO FINAL LISTO PARA PUBLICAR
(incluye el contenido completo sin modificaciones)"""

        result = await self.llm(context, prompt, temperature=0.4)

        # El final_output es contenido + schedule
        output = f"""# CONTENIDO GENERADO\n\n{final_content}\n\n---\n\n# ESTRATEGIA DE PUBLICACION\n\n{result}"""
        context.final_output = output
        context.pipeline_name = "CONTENT"
        self.log(context, f"Content pipeline completado ({len(final_content)} chars)")
        return context
