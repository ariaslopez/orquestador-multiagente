"""MetricsCalculatorAgent — calcula Sharpe, Sortino, drawdown, win rate, profit factor."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class MetricsCalculatorAgent(BaseAgent):
    name = "MetricsCalculatorAgent"
    description = "Calcula metricas cuantitativas: Sharpe, Sortino, drawdown, win rate, PF."

    async def run(self, context: AgentContext) -> AgentContext:
        trade_data = context.get_data('trade_data') or ''
        trade_meta = context.get_data('trade_meta') or {}
        self.log(context, "Calculando metricas de performance...")

        prompt = f"""Eres un quant analyst con experiencia en trading algoritmico crypto.

DATOS DE TRADING ({trade_meta.get('records', 'N/A')} registros de {trade_meta.get('source', '?')}):
{trade_data[:4000]}

Calcula y presenta las metricas de performance:

## METRICAS DE RETORNO
| Metrica | Valor | Interpretacion |
|---------|-------|----------------|
| PnL Total | $ | ... |
| PnL Promedio por Trade | $ | ... |
| Best Trade | $ | ... |
| Worst Trade | $ | ... |
| Return % Total | % | ... |

## METRICAS DE RIESGO
| Metrica | Valor | Benchmark Bueno |
|---------|-------|------------------|
| Win Rate | % | > 50% |
| Profit Factor | X | > 1.5 |
| Sharpe Ratio | X | > 1.0 |
| Sortino Ratio | X | > 1.5 |
| Max Drawdown | % | < 20% |
| Calmar Ratio | X | > 1.0 |

## DISTRIBUCION DE TRADES
- Total trades: N
- Trades ganadores: N (X%)
- Trades perdedores: N (X%)
- Trades break-even: N
- Duracion promedio del trade

## CONSISTENCIA
- Meses/semanas/dias con PnL positivo vs negativo
- Racha ganadora mas larga
- Racha perdedora mas larga

Si no hay datos suficientes para alguna metrica, indica 'N/D' con explicacion."""

        result = await self.llm(context, prompt, temperature=0.1)
        context.set_data('metrics', result)
        self.log(context, "Metricas calculadas")
        return context
