"""
Orchestrator — DEPRECATED desde v2.0.0.

Este módulo es código legado de la arquitectura v1.
NO se usa en ningún pipeline activo. El orquestador actual es core/maestro.py.

Se conserva para referencia histórica pero NO importar en código nuevo.
Será eliminado en v3.0.0.
"""
from __future__ import annotations
import logging
from typing import List, Optional
from .base_agent import BaseAgent
from .context import AgentContext

logger = logging.getLogger(__name__)

# DEPRECATED: use core.maestro.Maestro instead


class Orchestrator:
    """
    DEPRECATED — no usar en código nuevo.
    Ver core/maestro.py para la implementación actual.
    """

    def __init__(self):
        import warnings
        warnings.warn(
            "Orchestrator está deprecated. Usa core.maestro.Maestro en su lugar.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.pipelines: dict = {}
        self.default_pipeline: Optional[str] = None

    def register_pipeline(self, pipeline, default: bool = False):
        raise NotImplementedError("Usa core.maestro.Maestro._build_*_pipeline()")

    def run(self, query: str, pipeline_name: Optional[str] = None, **kwargs) -> AgentContext:
        raise NotImplementedError("Usa await core.maestro.Maestro.run(user_input=...)")

    def list_pipelines(self) -> List[str]:
        from core.maestro import Maestro
        return list(Maestro.TASK_KEYWORDS.keys())
