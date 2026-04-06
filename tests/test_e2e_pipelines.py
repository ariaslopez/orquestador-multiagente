"""Tests E2E para los 12 pipelines del sistema CLAW.

Estrategia:
- Mock del LLM (no consume tokens reales)
- Input sintetico por pipeline
- Valida shape del AgentContext resultante:
  - ctx.status == 'completed'
  - ctx.pipeline_name == expected
  - ctx.final_output es un string no vacio
  - ctx.total_tokens >= 0

Run: pytest tests/test_e2e_pipelines.py -v
"""
from __future__ import annotations
import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context import AgentContext
from core.maestro import Maestro


# Respuesta mock del LLM — suficiente para que cada agente avance
MOCK_LLM_RESPONSE = "[MOCK] Output generado correctamente para test E2E."


def _make_maestro() -> Maestro:
    return Maestro(memory_manager=None, environment="local")


async def _run_pipeline(task_type: str, user_input: str) -> AgentContext:
    """Ejecuta un pipeline con LLM mockeado y retorna el contexto final."""
    maestro = _make_maestro()
    # Mock BaseAgent.llm para que no llame a APIs reales
    with patch(
        "core.base_agent.BaseAgent.llm",
        new=AsyncMock(return_value=MOCK_LLM_RESPONSE),
    ), patch(
        "infrastructure.audit_logger.AuditLogger.log_agent_trace",
        new=MagicMock(),
    ):
        ctx = await maestro.run(
            user_input=user_input,
            task_type=task_type,
        )
    return ctx


PIPELINE_CASES = [
    ("dev",            "Crea un bot de Telegram que envia alertas de precio de BTC"),
    ("research",       "Analiza el potencial de inversion de Solana para Q3 2026"),
    ("content",        "Escribe un hilo de Twitter sobre el halving de Bitcoin"),
    ("office",         "Analiza el reporte de ventas del Q1 en formato Excel"),
    ("qa",             "Audita este repositorio de Python en busca de bugs y vulnerabilidades"),
    ("pm",             "Planifica el backlog para un SaaS de gestion de inventario"),
    ("trading",        "Analiza el performance del bot de scalping con este backtest"),
    ("analytics",      "Genera el reporte semanal de KPIs para nuestro SaaS B2B"),
    ("marketing",      "Crea la estrategia de marketing para el lanzamiento de nuestro producto"),
    ("product",        "Prioriza el backlog de features usando RICE score"),
    ("security_audit", "Realiza un threat model STRIDE para nuestra API REST"),
    ("design",         "Disenha el design system para una app fintech mobile"),
]


class TestE2EPipelines(unittest.IsolatedAsyncioTestCase):
    """Tests E2E: un test por pipeline, valida shape del AgentContext."""

    async def _assert_pipeline(self, task_type: str, user_input: str):
        ctx = await _run_pipeline(task_type, user_input)

        self.assertEqual(
            ctx.status, "completed",
            f"[{task_type}] ctx.status esperado 'completed', got '{ctx.status}'. "
            f"Error: {getattr(ctx, 'error', None)}",
        )
        self.assertEqual(
            ctx.pipeline_name, task_type,
            f"[{task_type}] ctx.pipeline_name esperado '{task_type}', got '{ctx.pipeline_name}'",
        )
        self.assertIsInstance(
            ctx.final_output, str,
            f"[{task_type}] ctx.final_output debe ser str",
        )
        self.assertGreater(
            len(ctx.final_output), 0,
            f"[{task_type}] ctx.final_output no debe ser vacio",
        )
        self.assertGreaterEqual(
            getattr(ctx, 'total_tokens', 0), 0,
            f"[{task_type}] total_tokens debe ser >= 0",
        )

    async def test_dev_pipeline(self):
        await self._assert_pipeline("dev", PIPELINE_CASES[0][1])

    async def test_research_pipeline(self):
        await self._assert_pipeline("research", PIPELINE_CASES[1][1])

    async def test_content_pipeline(self):
        await self._assert_pipeline("content", PIPELINE_CASES[2][1])

    async def test_office_pipeline(self):
        await self._assert_pipeline("office", PIPELINE_CASES[3][1])

    async def test_qa_pipeline(self):
        await self._assert_pipeline("qa", PIPELINE_CASES[4][1])

    async def test_pm_pipeline(self):
        await self._assert_pipeline("pm", PIPELINE_CASES[5][1])

    async def test_trading_pipeline(self):
        await self._assert_pipeline("trading", PIPELINE_CASES[6][1])

    async def test_analytics_pipeline(self):
        await self._assert_pipeline("analytics", PIPELINE_CASES[7][1])

    async def test_marketing_pipeline(self):
        await self._assert_pipeline("marketing", PIPELINE_CASES[8][1])

    async def test_product_pipeline(self):
        await self._assert_pipeline("product", PIPELINE_CASES[9][1])

    async def test_security_audit_pipeline(self):
        await self._assert_pipeline("security_audit", PIPELINE_CASES[10][1])

    async def test_design_pipeline(self):
        await self._assert_pipeline("design", PIPELINE_CASES[11][1])


if __name__ == "__main__":
    unittest.main()
