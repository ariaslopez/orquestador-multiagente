"""
qa_agent.py — Redirector de compatibilidad (v2.2.2)

Importa directamente desde el sub-pipeline agents/qa/.
Este módulo NO debe usarse en código nuevo.
"""
from agents.qa import __all__ as _qa_exports  # noqa: F401

# Importaciones explícitas para IDEs
try:
    from agents.qa.test_runner import TestRunnerAgent       # noqa: F401
    from agents.qa.bug_reporter import BugReporterAgent     # noqa: F401
except ImportError:
    pass  # sub-agentes aún en construcción — no rompe producción
