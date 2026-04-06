"""InsightGeneratorAgent — extrae insights de negocio accionables desde datos consolidados."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class InsightGeneratorAgent(BaseAgent):
    name = "InsightGeneratorAgent"
    description = "Extrae insights de negocio y patrones accionables desde datos consolidados."

    async def run(self, context: AgentContext) -> AgentContext:
        collected_data = context.get_data('collected_data') or ''
        self.log(context, "Generando insights de negocio...")

        prompt = f"""Eres un business analyst con 10 años de experiencia en growth analytics.

SOLICITUD: {context.user_input}

DATOS CONSOLIDADOS:
{collected_data[:3500]}

Genera insights accionables:

## TOP 5 INSIGHTS
(Ordenados por impacto potencial en el negocio)
1. **[Insight]**: descripción + evidencia cuantitativa

## PATRONES DETECTADOS
- Tendencias temporales
- Segmentos de usuarios/clientes destacables
- Correlaciones no obvias

## OPORTUNIDADES IDENTIFICADAS
| Oportunidad | Potencial | Esfuerzo | Confianza |
|-------------|-----------|----------|----------|

## ALERTAS
Anomalías o métricas que requieren atención urgente.

## HIPÓTESIS A VALIDAR
Qué experimentos o análisis adicionales se recomiendan."""

        result = await self.llm(context, prompt, temperature=0.2)
        context.set_data('insights', result)
        self.log(context, "Insights generados")
        return context
