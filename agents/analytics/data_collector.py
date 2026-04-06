"""DataCollectorAgent — consolida datos de múltiples fuentes para análisis."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class DataCollectorAgent(BaseAgent):
    name = "DataCollectorAgent"
    description = "Consolida y normaliza datos de múltiples fuentes para análisis de negocio."

    async def run(self, context: AgentContext) -> AgentContext:
        self.log(context, "Recopilando y consolidando fuentes de datos...")

        file_content = context.get_data('file_content') or ''
        extra = f"\n\nDATOS DE ARCHIVO:\n{file_content[:2000]}" if file_content else ''

        prompt = f"""Eres un data engineer senior.

SOLICITUD: {context.user_input}{extra}

Identifica y estructura las fuentes de datos relevantes:

## INVENTARIO DE FUENTES
| Fuente | Tipo | Disponibilidad | Formato | Frecuencia |
|--------|------|---------------|---------|------------|

## DATOS DISPONIBLES
Lista los datasets, métricas y KPIs que se pueden extraer.

## GAPS DE DATOS
Qué datos faltan y cómo obtenerlos.

## ESQUEMA DE CONSOLIDACIÓN
Cómo unificar las fuentes (joins, llaves, granularidad temporal).

## DATOS NORMALIZADOS
Presenta un resumen estructurado de los datos consolidados listos para análisis."""

        result = await self.llm(context, prompt, temperature=0.15)
        context.set_data('collected_data', result)
        self.log(context, "Datos consolidados correctamente")
        return context
