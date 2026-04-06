"""
Pipeline — DEPRECATED desde v2.0.0.

Este módulo es código legado de la arquitectura v1.
NO se usa en ningún pipeline activo. El router actual es core/pipeline_router.py.

Se conserva para referencia histórica pero NO importar en código nuevo.
Será eliminado en v3.0.0.
"""
from __future__ import annotations
from typing import List
from .base_agent import BaseAgent

# DEPRECATED: use core.pipeline_router.PipelineRouter instead


class Pipeline:
    """
    DEPRECATED — no usar en código nuevo.
    Ver core/pipeline_router.py para la implementación actual.
    """

    def __init__(self, name: str, description: str = "", mode: str = "sequential"):
        import warnings
        warnings.warn(
            "Pipeline está deprecated. Usa core.pipeline_router.PipelineRouter en su lugar.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.name = name
        self.description = description
        self.mode = mode
        self._agents: List[BaseAgent] = []
        self._parallel_agents: List[BaseAgent] = []

    def add_agent(self, agent: BaseAgent) -> "Pipeline":
        raise NotImplementedError("Usa core.maestro.Maestro._build_*_pipeline()")

    def add_parallel_agent(self, agent: BaseAgent) -> "Pipeline":
        raise NotImplementedError("Usa core.maestro.Maestro._build_research_pipeline()")

    @property
    def agents(self) -> List[BaseAgent]:
        return self._agents

    def __repr__(self) -> str:
        return f"<Pipeline DEPRECATED: {self.name}>"
