"""ELIMINADO en PR-2 (refactor/pr2-cleanup-stubs-migrate-v1-agents).

No existe pipeline 'doc' en el sistema CLAW v2.x.
Si necesitas generar documentación, usa el pipeline DEV con
la tarea explícita: 'genera documentación para <repo>'.
"""
raise ImportError(
    "agents.doc_agent fue eliminado en PR-2. "
    "No hay pipeline 'doc'. Usa pipeline DEV con tarea de documentación."
)
