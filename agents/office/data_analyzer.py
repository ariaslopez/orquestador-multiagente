"""DataAnalyzerAgent — analisis estadistico, patrones y anomalias en datos extraidos."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class DataAnalyzerAgent(BaseAgent):
    name = "DataAnalyzerAgent"
    description = "Analiza estadisticamente los datos extraidos: patrones, anomalias y metricas clave."

    async def run(self, context: AgentContext) -> AgentContext:
        file_content = context.get_data('file_content') or ''
        file_meta = context.get_data('file_meta') or {}
        file_name = file_meta.get('name', 'archivo')
        self.log(context, f"Analizando datos de {file_name}...")

        prompt = f"""Eres un data analyst senior con experiencia en business intelligence.

ARCHIVO: {file_name}
PETICION: {context.user_input}

CONTENIDO:
{file_content[:4000]}

Realiza un analisis completo:

## ESTADISTICAS DESCRIPTIVAS
- Para cada columna/campo numerico: min, max, promedio, mediana
- Para columnas categoricas: valores unicos, distribucion
- Registros totales vs registros con datos validos

## METRICAS CLAVE DEL NEGOCIO
(las 5-7 metricas mas importantes segun el contexto del archivo)
| Metrica | Valor | Unidad | Benchmark sugerido |
|---------|-------|--------|-------------------|

## PATRONES DETECTADOS
- Tendencias temporales (si hay fechas)
- Correlaciones entre variables
- Segmentos o clusters naturales en los datos

## ANOMALIAS Y OUTLIERS
- Valores atipicos con su magnitud
- Datos faltantes o inconsistentes
- Posibles errores de entrada

## CALIDAD DE LOS DATOS
- Score de completitud: X%
- Score de consistencia: X%
- Problemas encontrados"""

        result = await self.llm(context, prompt, temperature=0.15)
        context.set_data('data_analysis', result)
        self.log(context, "Analisis de datos completado")
        return context
