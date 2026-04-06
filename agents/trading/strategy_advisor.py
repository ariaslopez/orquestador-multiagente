"""StrategyAdvisorAgent — recomendaciones concretas de optimizacion con valores especificos."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class StrategyAdvisorAgent(BaseAgent):
    name = "StrategyAdvisorAgent"
    description = "Genera recomendaciones concretas de optimizacion del bot con valores especificos."

    async def run(self, context: AgentContext) -> AgentContext:
        metrics = context.get_data('metrics') or ''
        risk_analysis = context.get_data('risk_analysis') or ''
        trade_data = context.get_data('trade_data') or ''
        trade_meta = context.get_data('trade_meta') or {}
        self.log(context, "Generando recomendaciones estrategicas...")

        prompt = f"""Eres un quant trader senior y consultor de sistemas algoritmicos crypto.
Tu especialidad: convertir analisis de datos en mejoras concretas y ejecutables.

METRICAS:
{metrics[:1500]}

ANALISIS DE RIESGO:
{risk_analysis[:1500]}

SOLICITUD ORIGINAL: {context.user_input}

Genera el reporte final de optimizacion:

## DIAGNOSTICO EJECUTIVO
(3-4 frases resumiendo el estado del bot — escrito para el dueno del bot)

## OPTIMIZACIONES DE PARAMETROS
(Solo si hay datos suficientes — valores concretos, no rangos vagos)
| Parametro | Valor Actual | Valor Sugerido | Impacto Esperado |
|-----------|-------------|----------------|------------------|

## FILTROS ADICIONALES RECOMENDADOS
(reglas concretas para mejorar win rate o reducir drawdown)
1. Filtro de horario: evitar operar entre X:00 - X:00 UTC (porque...)
2. Filtro de volatilidad: ...
3. Filtro de tendencia: ...

## MEJORAS DE GESTION DE RIESGO
- Position sizing actual vs recomendado
- Stop loss: ajuste sugerido
- Take profit: ajuste sugerido
- Max trades simultaneos

## PROXIMOS PASOS ORDENADOS POR IMPACTO
| # | Accion | Impacto Esperado | Esfuerzo | Prioridad |
|---|--------|-----------------|---------|----------|
| 1 | ... | +X% win rate | 2h | CRITICA |

## BACKTEST SUGERIDO
(que parametros testear primero y en que periodo)"""

        result = await self.llm(context, prompt, temperature=0.2)

        # Reporte consolidado final
        output = f"""# REPORTE DE TRADING ANALYTICS\n**Fuente:** {trade_meta.get('source', 'N/A')} | **Registros:** {trade_meta.get('records', 'N/A')}\n\n---\n\n## METRICAS DE PERFORMANCE\n{metrics[:800]}\n\n---\n\n## ANALISIS DE RIESGO\n{risk_analysis[:600]}\n\n---\n\n{result}"""
        context.final_output = output
        context.pipeline_name = "TRADING"
        self.log(context, "TRADING pipeline completado")
        return context
