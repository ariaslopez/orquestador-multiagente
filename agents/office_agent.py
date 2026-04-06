"""
OfficeAgent — DEPRECATED desde v2.0.0 (Fase 8).

Reemplazado por el pipeline OFFICE con 3 sub-agentes en agents/office/:
  - file_reader.py
  - data_analyzer.py
  - report_writer.py

Este archivo se conserva para compatibilidad con tests legacy.
Será eliminado en v3.0.0.
"""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class OfficeAgent(BaseAgent):
    """DEPRECATED — usar agents/office/ sub-pipeline."""
    name = "OfficeAgent"
    description = "[DEPRECATED] Agente monolítico de office. Ver agents/office/."

    async def run(self, ctx: AgentContext) -> AgentContext:
        raise NotImplementedError(
            "OfficeAgent está deprecated. "
            "Usa el pipeline 'office' con sub-agentes en agents/office/"
        )
