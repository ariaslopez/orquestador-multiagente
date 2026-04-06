"""FeedbackSynthesizerAgent — síntesis de feedback de usuarios en insights de producto."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class FeedbackSynthesizerAgent(BaseAgent):
    name = "FeedbackSynthesizerAgent"
    description = "Sintetiza feedback de usuarios en patrones, pain points y oportunidades de producto."

    async def run(self, context: AgentContext) -> AgentContext:
        market_research = context.get_data('market_research') or ''
        file_content = context.get_data('file_content') or ''
        feedback_raw = file_content or context.user_input
        self.log(context, "Sintetizando feedback de usuarios...")

        prompt = f"""Eres un UX researcher sintetizando feedback para el equipo de producto.

SOLICITUD: {context.user_input}

CONTEXTO DE MERCADO:
{market_research[:1500]}

FEEDBACK / DATOS DE USUARIOS:
{feedback_raw[:2000]}

Sintetiza el feedback:

## PAIN POINTS PRINCIPALES
(Ordenados por frecuencia e intensidad)
| Pain Point | Frecuencia | Intensidad | Segmento afectado |
|------------|-----------|-----------|------------------|

## PATRONES DE COMPORTAMIENTO
Qué hacen los usuarios, cómo usan el producto, dónde se pierden.

## MOMENTOS AHA
Cuándo los usuarios sienten el valor del producto.

## SOLICITUDES MÁS FRECUENTES
Features o mejoras pedidas con mayor recurrencia.

## VERBATIMS CLAVE
Citas literales representativas (reales o inferidas del contexto).

## SEGMENTOS DE USUARIOS
| Segmento | Necesidad principal | Nivel de satisfacción | Riesgo de churn |
|---------|--------------------|--------------------|----------------|"""

        result = await self.llm(context, prompt, temperature=0.2)
        context.set_data('user_feedback', result)
        self.log(context, "Feedback sintetizado")
        return context
