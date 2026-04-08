"""
trading_agent.py — Redirector de compatibilidad (v2.2.2)

Importa directamente desde el sub-pipeline agents/trading/.
Este módulo NO debe usarse en código nuevo.
"""
from agents.trading.backtest_reader import BacktestReaderAgent      # noqa: F401
from agents.trading.metrics_calculator import MetricsCalculatorAgent # noqa: F401
from agents.trading.risk_analyzer import RiskAnalyzerAgent           # noqa: F401
from agents.trading.strategy_advisor import StrategyAdvisorAgent     # noqa: F401

__all__ = [
    "BacktestReaderAgent",
    "MetricsCalculatorAgent",
    "RiskAnalyzerAgent",
    "StrategyAdvisorAgent",
]
