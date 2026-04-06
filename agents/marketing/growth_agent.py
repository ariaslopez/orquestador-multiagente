"""GrowthAgent — diseña loops de adquisición, retención y pricing."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class GrowthAgent(BaseAgent):
    name = "GrowthAgent"
    description = "Diseña loops de crecimiento, estrategias de retención y estructura de pricing."

    async def run(self, context: AgentContext) -> AgentContext:
        strategy = context.get_data('marketing_strategy') or ''
        self.log(context, "Diseñando loops de crecimiento...")

        prompt = f"""Eres un growth hacker con experiencia en productos PLG (Product-Led Growth).

SOLICITUD: {context.user_input}

ESTRATEGIA:
{strategy[:1500]}

Diseña el motor de crecimiento:

## GROWTH LOOPS
- Loop viral: acción usuario → valor para otros → nuevos usuarios
- Loop de contenido: creación → distribución → descubrimiento → conversión
- Loop de datos: uso → mejora del producto → más uso

## ESTRATEGIA DE PRICING
| Plan | Precio | Target | Features clave | Límites |
|------|--------|--------|---------------|--------|

## RETENCIÓN (primeros 30 días)
- Día 1: acción de activación crítica
- Semana 1: hábito a formar
- Día 30: milestone de éxito

## EXPERIMENTOS DE CRECIMIENTO
| Experimento | Hipótesis | Métrica | Duración | Costo |
|-------------|-----------|---------|----------|-------|

## NORTH STAR METRIC
Una sola métrica que captura el valor entregado al usuario."""

        result = await self.llm(context, prompt, temperature=0.3)
        context.set_data('growth_strategy', result)
        self.log(context, "Estrategia de growth definida")
        return context
