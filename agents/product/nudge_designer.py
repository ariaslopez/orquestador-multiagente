"""NudgeDesignerAgent — diseña nudges de comportamiento para activación y retención."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class NudgeDesignerAgent(BaseAgent):
    name = "NudgeDesignerAgent"
    description = "Diseña nudges de comportamiento (onboarding, activación, retención) basados en behavioral design."

    async def run(self, context: AgentContext) -> AgentContext:
        user_feedback = context.get_data('user_feedback') or ''
        feature_priorities = context.get_data('feature_priorities') or ''
        self.log(context, "Diseñando nudges de comportamiento y producto final...")

        prompt = f"""Eres un behavioral designer experto en product-led growth y psicología del usuario.

SOLICITUD: {context.user_input}

FEEDBACK: {user_feedback[:1000]}
PRIORIDADES: {feature_priorities[:1000]}

Diseña los nudges y genera el reporte de producto final:

## NUDGES DE ONBOARDING
| Momento | Trigger | Nudge | Canal | Objetivo |
|---------|---------|-------|-------|----------|

## NUDGES DE ACTIVACIÓN
Acciones clave que el usuario debe completar en las primeras 24-72h.

## NUDGES DE RETENCIÓN
| Señal de riesgo | Intervención | Timing | Mensaje |
|----------------|-------------|--------|--------|

## LOOPS DE HÁBITO
Cue → Routine → Reward para el uso recurrente del producto.

# VISIÓN DE PRODUCTO — REPORTE FINAL

## RESUMEN EJECUTIVO
Estado del mercado, oportunidad y estrategia de producto en 5 frases.

## ROADMAP DE PRODUCTO (próximos 6 meses)
| Fase | Features | Objetivo | Métrica de éxito |
|------|---------|----------|------------------|

## HIPÓTESIS CENTRAL
Si construimos [X] para [segmento], lograremos [outcome] medido por [métrica]."""

        result = await self.llm(context, prompt, temperature=0.25)
        context.final_output = result
        context.pipeline_name = "PRODUCT"
        self.log(context, "Visión de producto completa — PRODUCT pipeline completado")
        return context
