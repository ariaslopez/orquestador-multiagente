"""
Smoke test — Fase 14: Supabase persistence — save/retrieve sesión

Cubre:
  - save_session() llama a supabase con los campos correctos
  - find_similar() retorna lista vacía si Supabase no responde (graceful degradation)
  - find_similar() retorna entradas cuando Supabase responde normalmente
  - save_session() con ctx que tiene failed_agents registra el estado de error
  - Supabase caído (exc) no propaga al llamador — retorna [] o None silenciosamente
  - Los campos session_id, task_type, status, duration son persistidos

No usa Supabase real — todo via patch y AsyncMock del cliente.

Ejecutar:
    pytest tests/smoke/test_supabase_persistence.py -v
"""
from __future__ import annotations
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from core.context import AgentContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _completed_ctx() -> AgentContext:
    ctx = AgentContext(user_input="analiza el backtest del bot")
    ctx.task_type = "trading"
    ctx.status = "completed"
    ctx.finish("completed")
    ctx.log("test_agent", "ejecución ok")
    return ctx


def _failed_ctx() -> AgentContext:
    ctx = AgentContext(user_input="crea un script de trading")
    ctx.task_type = "dev"
    ctx.error = "CoderAgent: timeout"
    ctx.mark_agent_failed("CoderAgent", "timeout")
    ctx.finish("failed")
    return ctx


# ---------------------------------------------------------------------------
# Test 1: save_session persiste los campos clave
# ---------------------------------------------------------------------------

def test_save_session_persists_key_fields():
    """save_session debe llamar a Supabase con session_id, task_type, status y duration."""
    from infrastructure.memory.supabase_memory import SupabaseMemoryManager

    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.execute = AsyncMock(return_value=MagicMock(data=[{"id": "abc"}]))

    ctx = _completed_ctx()

    with patch(
        "infrastructure.memory.supabase_memory.create_async_client",
        AsyncMock(return_value=mock_client),
    ):
        manager = SupabaseMemoryManager(
            url="https://test.supabase.co",
            key="test_anon_key",
        )
        asyncio.get_event_loop().run_until_complete(manager.save_session(ctx))

    # Verificar que se llamó a insert() con los campos mínimos esperados
    insert_calls = mock_table.insert.call_args_list
    assert len(insert_calls) >= 1, "Se esperaba al menos un insert"
    record = insert_calls[0][0][0]  # primer argumento del primer call
    assert record["session_id"] == ctx.session_id
    assert record["task_type"] == "trading"
    assert record["status"] == "completed"
    assert "duration_seconds" in record


# ---------------------------------------------------------------------------
# Test 2: save_session con ctx fallido registra error y failed_agents
# ---------------------------------------------------------------------------

def test_save_session_registers_failed_agents():
    """save_session debe persistir el campo error y la lista de failed_agents."""
    from infrastructure.memory.supabase_memory import SupabaseMemoryManager

    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.execute = AsyncMock(return_value=MagicMock(data=[]))

    ctx = _failed_ctx()

    with patch(
        "infrastructure.memory.supabase_memory.create_async_client",
        AsyncMock(return_value=mock_client),
    ):
        manager = SupabaseMemoryManager(
            url="https://test.supabase.co",
            key="test_anon_key",
        )
        asyncio.get_event_loop().run_until_complete(manager.save_session(ctx))

    record = mock_table.insert.call_args_list[0][0][0]
    assert record["status"] == "failed"
    assert "CoderAgent" in str(record.get("failed_agents", ""))
    assert record.get("error") == "CoderAgent: timeout"


# ---------------------------------------------------------------------------
# Test 3: Supabase caído en save → no propaga excepción
# ---------------------------------------------------------------------------

def test_save_session_does_not_raise_on_supabase_error():
    """Si Supabase lanza excepción en save, el manager no debe propagarla."""
    from infrastructure.memory.supabase_memory import SupabaseMemoryManager

    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.execute = AsyncMock(side_effect=ConnectionError("Supabase caído"))

    ctx = _completed_ctx()

    with patch(
        "infrastructure.memory.supabase_memory.create_async_client",
        AsyncMock(return_value=mock_client),
    ):
        manager = SupabaseMemoryManager(
            url="https://test.supabase.co",
            key="test_anon_key",
        )
        # No debe lanzar
        asyncio.get_event_loop().run_until_complete(manager.save_session(ctx))


# ---------------------------------------------------------------------------
# Test 4: find_similar retorna [] si Supabase no responde
# ---------------------------------------------------------------------------

def test_find_similar_returns_empty_on_error():
    """find_similar debe retornar [] si Supabase falla (graceful degradation)."""
    from infrastructure.memory.supabase_memory import SupabaseMemoryManager

    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute = AsyncMock(side_effect=RuntimeError("timeout"))

    with patch(
        "infrastructure.memory.supabase_memory.create_async_client",
        AsyncMock(return_value=mock_client),
    ):
        manager = SupabaseMemoryManager(
            url="https://test.supabase.co",
            key="test_anon_key",
        )
        result = asyncio.get_event_loop().run_until_complete(
            manager.find_similar("bot de trading", "trading")
        )

    assert result == [] or result is None, (
        "find_similar caído debe retornar lista vacía o None"
    )


# ---------------------------------------------------------------------------
# Test 5: find_similar retorna datos cuando Supabase responde
# ---------------------------------------------------------------------------

def test_find_similar_returns_data_on_success():
    """find_similar debe retornar la lista de entradas cuando Supabase responde bien."""
    from infrastructure.memory.supabase_memory import SupabaseMemoryManager

    fake_rows = [
        {"session_id": "abc", "task_type": "trading", "summary": "backtest BTC"},
        {"session_id": "def", "task_type": "trading", "summary": "sharpe ratio"},
    ]

    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute = AsyncMock(return_value=MagicMock(data=fake_rows))

    with patch(
        "infrastructure.memory.supabase_memory.create_async_client",
        AsyncMock(return_value=mock_client),
    ):
        manager = SupabaseMemoryManager(
            url="https://test.supabase.co",
            key="test_anon_key",
        )
        result = asyncio.get_event_loop().run_until_complete(
            manager.find_similar("backtest BTC", "trading")
        )

    assert len(result) == 2
    assert result[0]["session_id"] == "abc"
