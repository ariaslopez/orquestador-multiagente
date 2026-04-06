"""TradingAnalyticsAgent — Analiza logs de bots, backtests y performance de trading."""
from __future__ import annotations
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class TradingAnalyticsAgent(BaseAgent):
    name = "TradingAnalyticsAgent"
    description = "Analiza logs de bots de trading, backtests y sugiere mejoras de parametros."

    async def run(self, context: AgentContext) -> AgentContext:
        input_file = getattr(context, 'input_file', None)
        data_content = ''

        if input_file and Path(input_file).exists():
            ext = Path(input_file).suffix.lower()
            if ext == '.csv':
                import csv
                rows = []
                with open(input_file, encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        rows.append(str(dict(row)))
                        if i > 200:
                            rows.append('...(truncado)')
                            break
                data_content = '\n'.join(rows)
            else:
                data_content = Path(input_file).read_text(encoding='utf-8')[:4000]
            self.log(context, f"Analizando datos de trading: {input_file}")
        else:
            data_content = context.user_input

        prompt = f"""Eres un quant trader y analista de sistemas algoritmicos con experiencia en crypto.
Analiza los siguientes datos de trading:

{data_content[:4000]}

PETICION: {context.user_input}

Genera un reporte con:
## 1. METRICAS DE PERFORMANCE
   - Win rate, Profit Factor, Sharpe Ratio, Max Drawdown
   - PnL total, PnL promedio por trade

## 2. PATRONES DETECTADOS
   - Horas/dias con mejor performance
   - Activos mas rentables
   - Condiciones de mercado favorables/desfavorables

## 3. DEBILIDADES DEL SISTEMA
   - Donde pierde dinero consistentemente
   - Drawdowns y su causa probable

## 4. OPTIMIZACIONES SUGERIDAS
   - Parametros a ajustar con valores concretos
   - Filtros adicionales recomendados

## 5. PROXIMOS PASOS ACCIONABLES
   (lista ordenada por impacto esperado)"""
        report = await self.llm(context, prompt, temperature=0.2)
        context.final_output = report
        context.pipeline_name = "TRADING"
        self.log(context, "Analisis de trading completado")
        return context
