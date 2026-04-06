"""RiskAnalyzerAgent — analiza exposicion, concentracion de riesgo y drawdowns por activo."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class RiskAnalyzerAgent(BaseAgent):
    name = "RiskAnalyzerAgent"
    description = "Analiza riesgo: exposicion por activo, concentracion, drawdowns y correlaciones."

    async def run(self, context: AgentContext) -> AgentContext:
        trade_data = context.get_data('trade_data') or ''
        metrics = context.get_data('metrics') or ''
        self.log(context, "Analizando riesgo...")

        prompt = f"""Eres un risk manager especializado en portfolios de trading algoritmico crypto.

DATOS:
{trade_data[:2500]}

METRICAS CALCULADAS:
{metrics[:1000]}

Realiza el analisis de riesgo completo:

## EXPOSICION POR ACTIVO
| Activo | % del PnL | % de Trades | Avg PnL | Win Rate | Evaluacion |
|--------|-----------|-------------|---------|----------|------------|

## CONCENTRACION DE RIESGO
- El sistema depende demasiado de algun activo? (> 40% del PnL)
- Diversificacion actual vs recomendada

## ANALISIS DE DRAWDOWNS
- Drawdown maximo: duracion + recuperacion
- Drawdowns consecutivos
- Causa probable de los drawdowns principales (volatilidad, tendencia, horario)

## RIESGO POR CONDICION DE MERCADO
- Performance en mercado alcista vs bajista
- Performance en alta volatilidad vs baja
- Horas/dias del dia con mayor riesgo

## CORRELACIONES PELIGROSAS
- El bot pierde consistentemente en ciertos contextos?
- Hay patron de sobre-trading o under-trading?

## SCORE DE RIESGO GLOBAL: X/10
(1=muy riesgoso, 10=muy controlado)
Justificacion:"""

        result = await self.llm(context, prompt, temperature=0.1)
        context.set_data('risk_analysis', result)
        self.log(context, "Analisis de riesgo completado")
        return context
