"""
office_agent.py — Redirector de compatibilidad (v2.2.2)

Importa directamente desde el sub-pipeline agents/office/.
Este módulo NO debe usarse en código nuevo.
"""
try:
    from agents.office import __all__ as _office_exports  # noqa: F401
except ImportError:
    pass  # sub-agentes aún en construcción — no rompe producción
