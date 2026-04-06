"""
PMAgent — DEPRECATED desde v2.0.0 (Fase 8).

Reemplazado por el pipeline PM con 4 sub-agentes en agents/pm/:
  - requirements_parser.py
  - backlog_builder.py
  - sprint_planner.py
  - roadmap_generator.py

Este archivo se conserva para compatibilidad con tests legacy.
Será eliminado en v3.0.0.
"""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class PMAgent(BaseAgent):
    """DEPRECATED — usar agents/pm/ sub-pipeline."""
    name = "PMAgent"
    description = "[DEPRECATED] Agente monolítico de PM. Ver agents/pm/."

    async def run(self, ctx: AgentContext) -> AgentContext:
        raise NotImplementedError(
            "PMAgent está deprecated. "
            "Usa el pipeline 'pm' con sub-agentes en agents/pm/"
        )
