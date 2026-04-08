"""ELIMINADO en PR-2 (refactor/pr2-cleanup-stubs-migrate-v1-agents).

Este módulo era un redirector de compatibilidad.
Importar directamente desde agents.trading.<agente>.

Ejemplo:
    from agents.trading.data_agent import DataAgent
    from agents.trading.backtest_reader import BacktestReaderAgent
"""
raise ImportError(
    "agents.trading_agent fue eliminado en PR-2. "
    "Importa desde agents.trading.<agente> directamente."
)
