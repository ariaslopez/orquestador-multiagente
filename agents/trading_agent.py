"""
TradingAnalyticsAgent — DEPRECATED desde v2.0.0 (Fase 8).

Reemplazado por el pipeline TRADING con 4 sub-agentes en agents/trading/:
  - backtest_reader.py
  - metrics_calculator.py
  - risk_analyzer.py
  - strategy_advisor.py

Este archivo se conserva para compatibilidad con tests legacy.
Será eliminado en v3.0.0.
"""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class TradingAnalyticsAgent(BaseAgent):
    """DEPRECATED — usar agents/trading/ sub-pipeline."""
    name = "TradingAnalyticsAgent"
    description = "[DEPRECATED] Agente monolítico de trading. Ver agents/trading/."

    async def run(self, ctx: AgentContext) -> AgentContext:
        raise NotImplementedError(
            "TradingAnalyticsAgent está deprecated. "
            "Usa el pipeline 'trading' con sub-agentes en agents/trading/"
        )
