"""
Smoke tests críticos — PR-4

Cubren los cambios más importantes del PR-1:
  - Inyección de MCPHub en AgentContext
  - Proxy mcp_call en contexto
  - Clasificación de pipelines (DEV / RESEARCH / TRADING)
  - Hooks _before_run / _after_run son NO-OP sin MCPHub (retrocompatibilidad)

Ejecutar:
    pytest tests/smoke/test_mcp_context.py -v
"""
from __future__ import annotations
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from core.context import AgentContext


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ctx():
    return AgentContext(user_input="test input")


@pytest.fixture
def mock_hub():
    hub = MagicMock()
    hub.is_server_available = MagicMock(return_value=True)
    hub.call = AsyncMock(return_value={"result": "ok"})
    return hub


# ---------------------------------------------------------------------------
# Test 1: inject_mcp almacena el hub correctamente
# ---------------------------------------------------------------------------

def test_inject_mcp_on_context(ctx, mock_hub):
    """inject_mcp() debe almacenar el hub y hacer que is_mcp_available() funcione."""
    assert not ctx.is_mcp_available("brave_search"), "Sin hub, siempre False"
    ctx.inject_mcp(mock_hub)
    assert ctx.is_mcp_available("brave_search"), "Con hub disponible, debe ser True"


# ---------------------------------------------------------------------------
# Test 2: mcp_call proxea correctamente al hub
# ---------------------------------------------------------------------------

def test_mcp_call_proxy(ctx, mock_hub):
    """mcp_call() debe delegar al hub.call() con los parámetros correctos."""
    ctx.inject_mcp(mock_hub)
    result = asyncio.get_event_loop().run_until_complete(
        ctx.mcp_call("brave_search", "brave_web_search", {"query": "bitcoin"})
    )
    mock_hub.call.assert_called_once_with("brave_search", "brave_web_search", {"query": "bitcoin"})
    assert result == {"result": "ok"}


# ---------------------------------------------------------------------------
# Test 3: clasificación de pipelines vía keywords
# ---------------------------------------------------------------------------

def test_pipeline_classification():
    """PipelineRouter debe clasificar prompts comunes correctamente."""
    from core.pipeline_router import PipelineRouter

    cases = [
        ("crea un script en python para leer CSV", "DEV"),
        ("investiga el impacto de las tasas de interés", "RESEARCH"),
        ("analiza el backtest de mi estrategia BTC", "TRADING"),
        ("genera un post para LinkedIn sobre IA", "CONTENT"),
        ("crea el plan del sprint Q2", "PM"),
    ]

    router = PipelineRouter()
    for prompt, expected_pipeline in cases:
        detected = router.classify(prompt)
        assert detected == expected_pipeline, (
            f"Prompt: '{prompt}'\n"
            f"Esperado: {expected_pipeline}\n"
            f"Detectado: {detected}"
        )


# ---------------------------------------------------------------------------
# Test 4: hooks NO-OP sin MCPHub (retrocompatibilidad)
# ---------------------------------------------------------------------------

def test_base_agent_hooks_noop_without_mcp():
    """_before_run y _after_run no deben fallar si no hay MCPHub inyectado."""
    from core.base_agent import BaseAgent
    from core.context import AgentContext

    class DummyAgent(BaseAgent):
        name = "DummyAgent"
        description = "Test"
        async def run(self, ctx): return ctx

    agent = DummyAgent()
    ctx = AgentContext(user_input="test")
    # Sin MCPHub — no debe lanzar excepciones
    asyncio.get_event_loop().run_until_complete(agent._before_run(ctx))
    asyncio.get_event_loop().run_until_complete(agent._after_run(ctx))
