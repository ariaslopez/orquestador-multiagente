"""
QAAgent — DEPRECATED desde v2.0.0 (Fase 8).

Reemplazado por el pipeline QA con 5 sub-agentes en agents/qa/:
  - static_analyzer.py
  - bug_hunter.py
  - security_reviewer.py
  - performance_profiler.py
  - test_generator.py

Este archivo se conserva para compatibilidad con tests legacy.
Será eliminado en v3.0.0.
"""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class QAAgent(BaseAgent):
    """DEPRECATED — usar agents/qa/ sub-pipeline."""
    name = "QAAgent"
    description = "[DEPRECATED] Agente monolítico de QA. Ver agents/qa/."

    async def run(self, ctx: AgentContext) -> AgentContext:
        raise NotImplementedError(
            "QAAgent está deprecated. "
            "Usa el pipeline 'qa' con sub-agentes en agents/qa/"
        )
