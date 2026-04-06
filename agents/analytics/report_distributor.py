"""ReportDistributorAgent — formatea y distribuye el reporte de analytics."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class ReportDistributorAgent(BaseAgent):
    name = "ReportDistributorAgent"
    description = "Formatea insights en reportes ejecutivos listos para distribuir."

    async def run(self, context: AgentContext) -> AgentContext:
        insights = context.get_data('insights') or ''
        collected_data = context.get_data('collected_data') or ''
        self.log(context, "Formateando reporte final de analytics...")

        prompt = f"""Eres un director de analytics redactando el reporte semanal para stakeholders.

SOLICITUD: {context.user_input}

INSIGHTS:
{insights[:3000]}

Genera el reporte ejecutivo final:

# REPORTE DE ANALYTICS

## RESUMEN EJECUTIVO
(4-5 frases con los hallazgos más críticos. Para C-level, sin jerga técnica.)

## DASHBOARD DE KPIs
| KPI | Valor Actual | Período Anterior | Variación | Estado |
|-----|-------------|-----------------|-----------|--------|

## INSIGHTS CLAVE
(Top 3, con impacto estimado en negocio)

## ACCIONES RECOMENDADAS
| Acción | Owner sugerido | Plazo | Impacto esperado |
|--------|---------------|-------|------------------|

## PRÓXIMO REPORTE
Fecha sugerida y métricas a monitorear hasta entonces."""

        result = await self.llm(context, prompt, temperature=0.2)
        context.final_output = result
        context.pipeline_name = "ANALYTICS"
        self.log(context, "Reporte de analytics distribuido — ANALYTICS pipeline completado")
        return context
