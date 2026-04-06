"""
ContentAgent — DEPRECATED desde v2.0.0 (Fase 8).

Reemplazado por el pipeline CONTENT con 5 sub-agentes en agents/content/:
  - topic_agent.py
  - writer_agent.py
  - editor_agent.py
  - brand_agent.py
  - scheduler_agent.py

Este archivo se conserva para compatibilidad con tests legacy.
Será eliminado en v3.0.0.
"""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class ContentAgent(BaseAgent):
    """DEPRECATED — usar agents/content/ sub-pipeline."""
    name = "ContentAgent"
    description = "[DEPRECATED] Agente monolítico de contenido. Ver agents/content/."

    async def run(self, ctx: AgentContext) -> AgentContext:
        raise NotImplementedError(
            "ContentAgent está deprecated. "
            "Usa el pipeline 'content' con sub-agentes en agents/content/"
        )
