"""agents/ — Paquete raiz de agentes del sistema CLAW.

ORGANIZACIÓN (post PR-2):
  agents/dev/        — Pipeline DEV (Planner, Coder, Reviewer, ...)
  agents/research/   — Pipeline RESEARCH (WebScout, Summarizer, ...)
  agents/trading/    — Pipeline TRADING (Data, Backtest, Risk, ...)
  agents/content/    — Pipeline CONTENT (Writer, Editor, Formatter, ...)
  agents/qa/         — Pipeline QA (BugHunter, StaticAnalyzer, ...)
  agents/pm/         — Pipeline PM (BacklogBuilder, SprintPlanner, ...)
  agents/office/     — Pipeline OFFICE (FileReader, Scheduler, ...)
  agents/shared/     — Utilidades transversales (ResponseAgent, ...)

IMPORTS DIRECTOS (preferidos):
  from agents.dev.language_agent import LanguageAgent
  from agents.shared.response_agent import ResponseAgent

ALIASES DE COMPATIBILIDAD v1 (deprecados, se eliminarán en PR-3):
  from agents import LanguageAgent   # alias → agents.dev.LanguageAgent
  from agents import ResponseAgent   # alias → agents.shared.ResponseAgent
"""
import warnings

# --- Sub-paquetes v2 (imports directos recomendados) ---
from agents.dev.language_agent        import LanguageAgent      as LanguageAgent
from agents.dev.local_search_agent    import LocalSearchAgent   as LocalSearchAgent
from agents.dev.code_analyzer_agent   import CodeAnalyzerAgent  as CodeAnalyzerAgent
from agents.shared.response_agent     import ResponseAgent      as ResponseAgent


# --- Aliases de compatibilidad v1 (DEPRECADOS) ---
# Mantener hasta que todos los imports en maestro.py / pipelines estén actualizados.
# Se eliminarán en PR-3 junto con la limpieza de core/orchestrator.py.

class _DeprecatedAlias:
    """Helper para emitir DeprecationWarning en el primer acceso."""
    def __init__(self, real_cls, old_name: str, new_import: str):
        self._cls        = real_cls
        self._old        = old_name
        self._new        = new_import

    def __call__(self, *args, **kwargs):
        warnings.warn(
            f"{self._old} importado desde agents/ está deprecado. "
            f"Usa: from {self._new} import {self._cls.__name__}",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._cls(*args, **kwargs)

    def __instancecheck__(cls, instance):
        return isinstance(instance, cls._cls)


# SearchAgent → LocalSearchAgent (renombrado)
SearchAgent = _DeprecatedAlias(
    LocalSearchAgent,
    "SearchAgent",
    "agents.dev.local_search_agent",
)
# CodeAgent → CodeAnalyzerAgent (renombrado)
CodeAgent = _DeprecatedAlias(
    CodeAnalyzerAgent,
    "CodeAgent",
    "agents.dev.code_analyzer_agent",
)


__all__ = [
    # v2 preferidos
    "LanguageAgent",
    "LocalSearchAgent",
    "CodeAnalyzerAgent",
    "ResponseAgent",
    # aliases v1 deprecados
    "SearchAgent",
    "CodeAgent",
]
