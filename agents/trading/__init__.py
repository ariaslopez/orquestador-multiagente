"""
TRADING pipeline — sub-agentes (v2.2.2)

Flujo de datos:
  DataAgent
      ↓ market_data, market_snapshot, market_symbol
  BacktestReaderAgent
      ↓ backtest_raw, backtest_summary
  MetricsCalculatorAgent
      ↓ metrics (win_rate, sharpe, max_drawdown, profit_factor)
  RiskAnalyzerAgent
      ↓ risk_report (risk_score, alerts[], recommendations[])
  StrategyAdvisorAgent
      ↓ strategy_advice (summary, actions[], confidence)

Uso en maestro.py:
    from agents.trading import (
        DataAgent,
        BacktestReaderAgent,
        MetricsCalculatorAgent,
        RiskAnalyzerAgent,
        StrategyAdvisorAgent,
    )
"""
from agents.trading.data_agent import DataAgent
from agents.trading.backtest_reader import BacktestReaderAgent
from agents.trading.metrics_calculator import MetricsCalculatorAgent
from agents.trading.risk_analyzer import RiskAnalyzerAgent
from agents.trading.strategy_advisor import StrategyAdvisorAgent

__all__ = [
    "DataAgent",
    "BacktestReaderAgent",
    "MetricsCalculatorAgent",
    "RiskAnalyzerAgent",
    "StrategyAdvisorAgent",
]
