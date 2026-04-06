"""MarketResearcherAgent — análisis competitivo y de mercado."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class MarketResearcherAgent(BaseAgent):
    name = "MarketResearcherAgent"
    description = "Realiza análisis competitivo, TAM/SAM/SOM y landscape de mercado."

    async def run(self, context: AgentContext) -> AgentContext:
        self.log(context, "Investigando mercado y competencia...")

        prompt = f"""Eres un product strategist especializado en investigación de mercado.

SOLICITUD: {context.user_input}

Realiza el análisis de mercado completo:

## DEFINICIÓN DEL MERCADO
- TAM (Total Addressable Market): estimación y fuente
- SAM (Serviceable Addressable Market): segmento alcanzable
- SOM (Serviceable Obtainable Market): objetivo realista año 1-3

## ANÁLISIS COMPETITIVO
| Competidor | Precio | Fortalezas | Debilidades | Cuota estimada |
|------------|--------|-----------|------------|----------------|

## MAPA DE POSICIONAMIENTO
Ejes principales del mercado y dónde se ubica cada jugador.

## JOBS TO BE DONE
Top 5 trabajos que los clientes contratan este tipo de producto.

## TENDENCIAS DE MERCADO
- Tendencias que favorecen la oportunidad
- Tendencias que representan amenaza

## VENTANA DE OPORTUNIDAD
Por qué ahora es el momento adecuado para este producto."""

        result = await self.llm(context, prompt, temperature=0.25)
        context.set_data('market_research', result)
        self.log(context, "Investigación de mercado completada")
        return context
