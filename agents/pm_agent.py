"""ELIMINADO en PR-2 (refactor/pr2-cleanup-stubs-migrate-v1-agents).

Importar directamente desde agents.pm.<agente>.

Ejemplo:
    from agents.pm.backlog_builder import BacklogBuilderAgent
"""
raise ImportError(
    "agents.pm_agent fue eliminado en PR-2. "
    "Importa desde agents.pm.<agente> directamente."
)
