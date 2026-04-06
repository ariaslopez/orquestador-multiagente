"""ReportWriterAgent — genera reporte ejecutivo estructurado con recomendaciones accionables."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class ReportWriterAgent(BaseAgent):
    name = "ReportWriterAgent"
    description = "Genera el reporte ejecutivo final con hallazgos, visualizaciones sugeridas y recomendaciones."

    async def run(self, context: AgentContext) -> AgentContext:
        data_analysis = context.get_data('data_analysis') or ''
        file_meta = context.get_data('file_meta') or {}
        file_name = file_meta.get('name', 'archivo')
        self.log(context, "Redactando reporte ejecutivo...")

        prompt = f"""Eres un consultor de datos senior redactando un reporte ejecutivo.

ARCHIVO ANALIZADO: {file_name}
SOLICITUD: {context.user_input}

ANALISIS DE DATOS:
{data_analysis[:3500]}

Genera el reporte ejecutivo completo:

# REPORTE DE ANALISIS — {file_name.upper()}

## RESUMEN EJECUTIVO
(3-4 frases con los hallazgos mas importantes. Escrito para un C-level.)

## HALLAZGOS PRINCIPALES
(Los 5 hallazgos mas relevantes, ordenados por impacto)
1. ...

## METRICAS CLAVE
(Tabla resumen en markdown con los KPIs mas importantes)

## VISUALIZACIONES RECOMENDADAS
(Que graficas generarias y por que — no las generes, solo sugierelas)
- Grafica 1: tipo, ejes, insight que revela

## ALERTAS Y RIESGOS
(Problemas que requieren atencion inmediata)

## RECOMENDACIONES DE ACCION
| # | Accion | Impacto | Esfuerzo | Prioridad |
|---|--------|---------|---------|----------|

## PROXIMOS PASOS
(3-5 acciones concretas con owner y plazo sugerido)"""

        result = await self.llm(context, prompt, temperature=0.2)
        context.final_output = result
        context.pipeline_name = "OFFICE"
        self.log(context, "Reporte ejecutivo generado — OFFICE pipeline completado")
        return context
