"""StrategyAgent — diseña estrategia de contenido y canales de marketing."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class MarketingStrategyAgent(BaseAgent):
    name = "MarketingStrategyAgent"
    description = "Diseña estrategia de marketing: canales, audiencias y mensajes clave."

    async def run(self, context: AgentContext) -> AgentContext:
        self.log(context, "Diseñando estrategia de marketing...")

        prompt = f"""Eres un CMO con experiencia en SaaS y productos digitales.

SOLICITUD: {context.user_input}

Diseña la estrategia de marketing completa:

## ICP (Ideal Customer Profile)
- Demografía, psicografía, pain points, job-to-be-done

## POSICIONAMIENTO
- Propuesta de valor única (1 frase)
- Diferenciadores vs competencia
- Mensaje core por segmento

## CANALES PRIORITARIOS
| Canal | Audiencia | CAC estimado | Prioridad | Táctica principal |
|-------|-----------|-------------|-----------|------------------|

## FUNNEL DE CONVERSIÓN
Awareness → Consideration → Decision → Retention (acciones por etapa)

## OKRs DE MARKETING
| Objetivo | KR1 | KR2 | Plazo |
|----------|-----|-----|-------|

## BUDGET ALLOCATION
Distribución recomendada del presupuesto por canal (%)."""

        result = await self.llm(context, prompt, temperature=0.3)
        context.set_data('marketing_strategy', result)
        self.log(context, "Estrategia de marketing definida")
        return context
