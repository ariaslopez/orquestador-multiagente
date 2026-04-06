"""FeaturePrioritizerAgent — priorización data-driven de features con RICE/MoSCoW."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class FeaturePrioritizerAgent(BaseAgent):
    name = "FeaturePrioritizerAgent"
    description = "Prioriza features con frameworks RICE y MoSCoW basados en datos de mercado y feedback."

    async def run(self, context: AgentContext) -> AgentContext:
        market_research = context.get_data('market_research') or ''
        user_feedback = context.get_data('user_feedback') or ''
        self.log(context, "Priorizando features con RICE/MoSCoW...")

        prompt = f"""Eres un Senior Product Manager priorizando el roadmap con datos.

SOLICITUD: {context.user_input}

MERCADO: {market_research[:1200]}
FEEDBACK: {user_feedback[:1200]}

Prioriza el backlog de producto:

## PRIORIZACIÓN RICE
| Feature | Reach | Impact | Confidence | Effort | RICE Score |
|---------|-------|--------|-----------|--------|------------|
(Reach: usuarios/mes, Impact: 0.25-3x, Confidence: %, Effort: semanas-persona)

## CLASIFICACIÓN MOSCOW
**Must Have** (sin esto el producto no funciona):
**Should Have** (importante pero no bloqueante):
**Could Have** (nice to have):
**Won't Have** (descartado por ahora):

## TOP 3 FEATURES A CONSTRUIR PRIMERO
Justificación por cada una con evidencia del feedback y mercado.

## DEPENDENCIAS TÉCNICAS
Qué features dependen de otras para poder construirse.

## RIESGOS DE PRIORIZACIÓN
Qué pasa si nos equivocamos en el orden."""

        result = await self.llm(context, prompt, temperature=0.2)
        context.set_data('feature_priorities', result)
        self.log(context, "Features priorizadas")
        return context
