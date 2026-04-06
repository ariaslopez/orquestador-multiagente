"""ThesisAgent — Sintetiza el analisis en una tesis de inversion estructurada."""
from __future__ import annotations
from datetime import date
from core.base_agent import BaseAgent
from core.context import AgentContext


class ThesisAgent(BaseAgent):
    name = "ThesisAgent"
    description = "Genera la tesis de inversion final con bull/bear case y riesgos."

    async def run(self, context: AgentContext) -> AgentContext:
        analysis = context.get_data('analysis', '')
        if not analysis:
            self.log(context, "⚠ Sin analisis previo — ThesisAgent no puede generar tesis")
            context.final_output = "Error: AnalystAgent no produjo analisis. Verifica los datos de entrada."
            return context

        self.log(context, "Generando tesis de inversion...")
        today = date.today().isoformat()
        prompt = f"""Eres un analista de investigacion institucional (no das recomendaciones de compra/venta).
Basandote en el siguiente analisis, genera una tesis de inversion completa.

TEMA: {context.user_input}
FECHA: {today}

ANALISIS BASE:
{analysis}

Estructura de la tesis:
# TESIS: [TITULO]
**Fecha:** {today} | **Tipo:** Analisis de Investigacion

## Resumen Ejecutivo
(3-4 oraciones con la tesis central)

## Bull Case
(argumentos alcistas con datos concretos)

## Bear Case
(riesgos y argumentos bajistas)

## Metricas Clave
(tabla con datos numericos relevantes)

## Riesgos Principales
(lista de riesgos ordenados por impacto)

## Conclusion del Analisis
(sintesis objetiva sin recomendacion de accion)

---
*Este documento es solo para fines informativos y no constituye asesoramiento financiero.*"""
        thesis = await self.llm(context, prompt, temperature=0.3)
        context.set_data('thesis', thesis)
        context.final_output = thesis
        context.pipeline_name = "RESEARCH"
        self.log(context, f"Tesis generada ({len(thesis)} chars)")
        return context
