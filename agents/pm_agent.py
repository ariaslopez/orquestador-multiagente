"""
pm_agent.py — Redirector de compatibilidad (v2.2.2)

Importa directamente desde el sub-pipeline agents/pm/.
Este módulo NO debe usarse en código nuevo.
"""
try:
    from agents.pm import __all__ as _pm_exports  # noqa: F401
except ImportError:
    pass  # sub-agentes aún en construcción — no rompe producción
