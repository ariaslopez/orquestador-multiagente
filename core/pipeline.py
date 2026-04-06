"""Pipeline — Definición declarativa de un pipeline de agentes."""
from __future__ import annotations
from typing import List, Optional
from .base_agent import BaseAgent


class Pipeline:
    """
    Definición declarativa de un pipeline.
    Se usa para registrar y describir pipelines,
    la ejecución real la hace el PipelineRouter.
    """

    def __init__(self, name: str, description: str = "", mode: str = "sequential"):
        self.name = name
        self.description = description
        self.mode = mode  # sequential | parallel_then_sequential
        self._agents: List[BaseAgent] = []
        self._parallel_agents: List[BaseAgent] = []

    def add_agent(self, agent: BaseAgent) -> "Pipeline":
        """Agrega un agente al pipeline (builder pattern)."""
        self._agents.append(agent)
        return self

    def add_parallel_agent(self, agent: BaseAgent) -> "Pipeline":
        """Agrega un agente al grupo paralelo."""
        self._parallel_agents.append(agent)
        return self

    @property
    def agents(self) -> List[BaseAgent]:
        return self._agents

    @property
    def parallel_agents(self) -> List[BaseAgent]:
        return self._parallel_agents

    def __repr__(self) -> str:
        return f"<Pipeline: {self.name} | {len(self._agents)} agents | mode={self.mode}>"
