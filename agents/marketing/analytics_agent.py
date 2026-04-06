"""MarketingAnalyticsAgent — calcula métricas de marketing (CAC, LTV, ROAS)."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class MarketingAnalyticsAgent(BaseAgent):
    name = "MarketingAnalyticsAgent"
    description = "Calcula y analiza métricas de marketing: CAC, LTV, ROAS, churn y cohorts."

    async def run(self, context: AgentContext) -> AgentContext:
        strategy = context.get_data('marketing_strategy') or ''
        growth = context.get_data('growth_strategy') or ''
        copy = context.get_data('marketing_copy') or ''
        self.log(context, "Calculando métricas y generando plan final...")

        prompt = f"""Eres un marketing analyst consolidando el plan de marketing completo.

SOLICITUD: {context.user_input}

ESTRATEGIA: {strategy[:1000]}
GROWTH: {growth[:1000]}
COPY: {copy[:500]}

Genera el plan de marketing ejecutivo final:

# PLAN DE MARKETING COMPLETO

## MÉTRICAS OBJETIVO
| Métrica | Fórmula | Benchmark industria | Target mes 3 | Target mes 12 |
|---------|---------|--------------------|-----------|--------------|
| CAC | costo adq / nuevos clientes | | | |
| LTV | ARPU × vida útil | | | |
| LTV/CAC | ratio | >3x ideal | | |
| Churn rate | | | | |
| MRR growth | | | | |

## ROADMAP DE MARKETING (90 días)
| Semana | Actividad | Canal | Métrica de éxito |
|--------|-----------|-------|------------------|

## STACK DE MARKETING
Herramientas recomendadas por categoría (analytics, email, ads, CRM).

## RIESGOS Y MITIGACIONES
Top 3 riesgos del plan con su plan de contingencia."""

        result = await self.llm(context, prompt, temperature=0.2)
        context.final_output = result
        context.pipeline_name = "MARKETING"
        self.log(context, "Plan de marketing completo — MARKETING pipeline completado")
        return context
