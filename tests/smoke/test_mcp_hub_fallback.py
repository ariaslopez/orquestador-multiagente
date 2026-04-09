"""
Smoke test — Fase 14: MCPHub fallback — resiliencia ante fallos de MCP

Cubre:
  - MCP caído (adapter.call lanza Exception) → retorna None sin romper el agente
  - Env key faltante o con valor placeholder → retorna None sin llamar adapter
  - Timeout del adapter (→ asyncio.TimeoutError) → retorna None
  - MCP no registrado en REGISTRY → retorna None
  - MCPs sin required_env (mcp_memory, sequential_thinking, coingecko, semgrep, playwright)
    → se intentan siempre (no hay env guard)
  - available() filtra correctamente por env y categoria
  - status() devuelve 'ready' o 'missing:<ENV>'

No usa red real — todo via patch y AsyncMock.

Ejecutar:
    pytest tests/smoke/test_mcp_hub_fallback.py -v
"""
from __future__ import annotations
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.mcp_hub import MCPHub


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def hub():
    return MCPHub()


# ---------------------------------------------------------------------------
# Test 1: adapter.call lanza Exception → retorna None (no propaga)
# ---------------------------------------------------------------------------

def test_mcp_call_returns_none_on_adapter_exception(hub):
    """Si adapter.call lanza una excepción, MCPHub debe retornar None silenciosamente."""
    broken_adapter = MagicMock()
    broken_adapter.call = AsyncMock(side_effect=RuntimeError("adapter roto"))

    with patch("infrastructure.mcp_hub._load_adapter", return_value=broken_adapter):
        result = asyncio.get_event_loop().run_until_complete(
            hub.call("mcp_memory", "retrieve", {"key": "x"})
        )

    assert result is None, "Adapter roto debe retornar None, no propagar excepción"


# ---------------------------------------------------------------------------
# Test 2: env key faltante → retorna None sin llamar al adapter
# ---------------------------------------------------------------------------

def test_mcp_call_returns_none_when_env_missing(hub, monkeypatch):
    """Si la env key requerida no está configurada, no debe intentar llamar al adapter."""
    # brave_search requiere BRAVE_API_KEY
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)

    adapter_spy = MagicMock()
    adapter_spy.call = AsyncMock(return_value={"result": "ok"})

    with patch("infrastructure.mcp_hub._load_adapter", return_value=adapter_spy) as mock_load:
        result = asyncio.get_event_loop().run_until_complete(
            hub.call("brave_search", "search", {"query": "bitcoin"})
        )

    assert result is None
    mock_load.assert_not_called()  # ni siquiera cargó el adapter


# ---------------------------------------------------------------------------
# Test 3: env key con valor placeholder → retorna None
# ---------------------------------------------------------------------------

def test_mcp_call_returns_none_when_env_is_placeholder(hub, monkeypatch):
    """Un valor 'your_*' en la env key debe tratarse como no configurado."""
    monkeypatch.setenv("BRAVE_API_KEY", "your_brave_api_key_here")

    result = asyncio.get_event_loop().run_until_complete(
        hub.call("brave_search", "search", {"query": "test"})
    )
    assert result is None


# ---------------------------------------------------------------------------
# Test 4: timeout del adapter → retorna None
# ---------------------------------------------------------------------------

def test_mcp_call_returns_none_on_timeout(hub):
    """Si asyncio.wait_for expira, MCPHub debe retornar None sin propagar."""
    import asyncio as _asyncio

    async def slow_call(tool, params):
        await _asyncio.sleep(999)  # nunca termina
        return {}

    slow_adapter = MagicMock()
    slow_adapter.call = slow_call

    with patch("infrastructure.mcp_hub._load_adapter", return_value=slow_adapter):
        result = asyncio.get_event_loop().run_until_complete(
            hub.call("mcp_memory", "retrieve", {"key": "x"}, timeout=1)
        )

    assert result is None, "Timeout debe retornar None silenciosamente"


# ---------------------------------------------------------------------------
# Test 5: MCP no registrado → retorna None
# ---------------------------------------------------------------------------

def test_mcp_call_unknown_server_returns_none(hub):
    """Llamar a un servidor no registrado en REGISTRY debe retornar None."""
    result = asyncio.get_event_loop().run_until_complete(
        hub.call("servidor_fantasma", "tool", {})
    )
    assert result is None


# ---------------------------------------------------------------------------
# Test 6: MCPs sin required_env se intentan siempre
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("server", [
    "mcp_memory",
    "sequential_thinking",
    "coingecko",
    "semgrep",
    "playwright",
])
def test_no_env_mcps_attempt_adapter(hub, server):
    """
    MCPs sin required_env no deben ser bloqueados por el env guard.
    Deben llegar a _load_adapter (aunque éste falle).
    """
    good_adapter = MagicMock()
    good_adapter.call = AsyncMock(return_value={"ok": True})

    with patch("infrastructure.mcp_hub._load_adapter", return_value=good_adapter) as mock_load:
        result = asyncio.get_event_loop().run_until_complete(
            hub.call(server, "any_tool", {})
        )

    mock_load.assert_called_once_with(server)
    assert result == {"ok": True}


# ---------------------------------------------------------------------------
# Test 7: available() filtra por env configurada
# ---------------------------------------------------------------------------

def test_available_filters_by_configured_env(hub, monkeypatch):
    """available() debe incluir solo MCPs con env configurada."""
    # Sin ninguna env seteada: solo MCPs sin required_env deben estar disponibles
    env_keys = [
        "BRAVE_API_KEY", "CONTEXT7_API_KEY", "DEEPWIKI_API_KEY",
        "SUPABASE_URL", "OKX_API_KEY", "GITHUB_TOKEN",
        "SLACK_BOT_TOKEN", "N8N_WEBHOOK_URL",
    ]
    for key in env_keys:
        monkeypatch.delenv(key, raising=False)

    available = hub.available()
    no_env_mcps = {
        name for name, meta in hub.REGISTRY.items()
        if not meta.get("required_env")
    }
    assert set(available) == no_env_mcps, (
        f"Sin envs configuradas, solo deben estar disponibles: {no_env_mcps}\n"
        f"Obtenido: {set(available)}"
    )


# ---------------------------------------------------------------------------
# Test 8: available() filtra por categoria
# ---------------------------------------------------------------------------

def test_available_filters_by_category(hub, monkeypatch):
    """available(category='memory') debe retornar solo MCPs de esa categoría."""
    # mcp_memory no requiere env → siempre disponible
    memory_mcps = hub.available(category="memory")
    assert "mcp_memory" in memory_mcps
    for name in memory_mcps:
        assert hub.REGISTRY[name]["category"] == "memory"


# ---------------------------------------------------------------------------
# Test 9: status() retorna 'ready' o 'missing:<ENV>'
# ---------------------------------------------------------------------------

def test_status_reports_ready_and_missing(hub, monkeypatch):
    """status() debe reportar 'ready' para MCPs sin env, y 'missing:KEY' para los que no estén."""
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    status = hub.status()

    # mcp_memory: sin required_env → 'ready'
    assert status["mcp_memory"] == "ready"
    # sequential_thinking: sin required_env → 'ready'
    assert status["sequential_thinking"] == "ready"
    # brave_search: sin env → 'missing:BRAVE_API_KEY'
    assert status["brave_search"] == "missing:BRAVE_API_KEY"
