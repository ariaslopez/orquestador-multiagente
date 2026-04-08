"""ELIMINADO en PR-2 (refactor/pr2-cleanup-stubs-migrate-v1-agents).

Importar directamente desde agents.qa.<agente>.

Ejemplo:
    from agents.qa.bug_hunter import BugHunterAgent
    from agents.qa.static_analyzer import StaticAnalyzerAgent
"""
raise ImportError(
    "agents.qa_agent fue eliminado en PR-2. "
    "Importa desde agents.qa.<agente> directamente."
)
