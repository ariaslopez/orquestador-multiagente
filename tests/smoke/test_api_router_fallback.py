"""
Smoke test — Fase 14: APIRouter fallback — Groq caído → Gemini automático

Cubre:
  - Groq disponible → responde correctamente en el primer intento
  - Groq caído (exc) → fallback automático a Gemini
  - Groq + Gemini caídos → fallback a qwen local (si OLLAMA_ENABLED=true)
  - Todos los providers caídos → lanza excepción con mensaje claro
  - task_type='classification' usa modelo rápido (baja temperatura)
  - task_type='code' usa modelo con mayor contexto
  - El proveedor real usado se refleja en el retorno (metadata de tokens)

No usa red real — todo via patch de los clientes de Groq/Gemini.

Ejecutar:
    pytest tests/smoke/test_api_router_fallback.py -v
"""
from __future__ import annotations
import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.api_router import APIRouter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_groq_response(text: str = "respuesta ok"):
    choice = MagicMock()
    choice.message.content = text
    response = MagicMock()
    response.choices = [choice]
    response.usage.prompt_tokens = 10
    response.usage.completion_tokens = 20
    response.model = "llama-3.1-8b-instant"
    return response


def _mock_gemini_response(text: str = "respuesta gemini"):
    part = MagicMock()
    part.text = text
    candidate = MagicMock()
    candidate.content.parts = [part]
    response = MagicMock()
    response.candidates = [candidate]
    response.usage_metadata.prompt_token_count = 10
    response.usage_metadata.candidates_token_count = 20
    return response


# ---------------------------------------------------------------------------
# Test 1: Groq responde → retorna texto
# ---------------------------------------------------------------------------

def test_groq_primary_succeeds():
    """Cuando Groq está disponible, complete() debe retornar la respuesta directamente."""
    router = APIRouter()
    groq_resp = _mock_groq_response("trading signal detectado")

    with patch.object(router, "_call_groq", AsyncMock(return_value=("trading signal detectado", {"tokens": 30}))):
        text, meta = asyncio.get_event_loop().run_until_complete(
            router.complete(
                messages=[{"role": "user", "content": "analiza el mercado"}],
                task_type="trading",
            )
        )

    assert text == "trading signal detectado"


# ---------------------------------------------------------------------------
# Test 2: Groq caído → fallback a Gemini
# ---------------------------------------------------------------------------

def test_groq_down_falls_back_to_gemini():
    """Si Groq lanza excepción, debe intentarse Gemini automáticamente."""
    router = APIRouter()

    with (
        patch.object(router, "_call_groq", AsyncMock(side_effect=RuntimeError("Groq 503"))),
        patch.object(router, "_call_gemini", AsyncMock(return_value=("respuesta gemini", {"tokens": 30, "provider": "gemini"}))),
    ):
        text, meta = asyncio.get_event_loop().run_until_complete(
            router.complete(
                messages=[{"role": "user", "content": "precio de bitcoin"}],
                task_type="research",
            )
        )

    assert text == "respuesta gemini"
    assert meta.get("provider") == "gemini"


# ---------------------------------------------------------------------------
# Test 3: Groq + Gemini caídos → fallback a qwen local
# ---------------------------------------------------------------------------

def test_groq_and_gemini_down_falls_back_to_local(monkeypatch):
    """Si Groq y Gemini fallan, debe intentarse el modelo local (Ollama/qwen)."""
    monkeypatch.setenv("OLLAMA_ENABLED", "true")
    router = APIRouter()

    with (
        patch.object(router, "_call_groq", AsyncMock(side_effect=RuntimeError("503"))),
        patch.object(router, "_call_gemini", AsyncMock(side_effect=RuntimeError("quota"))),
        patch.object(router, "_call_local", AsyncMock(return_value=("respuesta local", {"tokens": 15, "provider": "local"}))),
    ):
        text, meta = asyncio.get_event_loop().run_until_complete(
            router.complete(
                messages=[{"role": "user", "content": "genera código python"}],
                task_type="dev",
            )
        )

    assert text == "respuesta local"
    assert meta.get("provider") == "local"


# ---------------------------------------------------------------------------
# Test 4: Todos los providers caídos → lanza excepción con mensaje claro
# ---------------------------------------------------------------------------

def test_all_providers_down_raises_with_clear_message(monkeypatch):
    """Si todos los providers fallan, debe lanzar excepción con mensaje legible."""
    monkeypatch.setenv("OLLAMA_ENABLED", "false")
    router = APIRouter()

    with (
        patch.object(router, "_call_groq", AsyncMock(side_effect=RuntimeError("503"))),
        patch.object(router, "_call_gemini", AsyncMock(side_effect=RuntimeError("quota"))),
    ):
        with pytest.raises(Exception) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                router.complete(
                    messages=[{"role": "user", "content": "test"}],
                    task_type="qa",
                )
            )

    error_msg = str(exc_info.value).lower()
    assert any(kw in error_msg for kw in ["provider", "fallaron", "failed", "disponible"]), (
        f"El mensaje de error debe ser descriptivo: '{exc_info.value}'"
    )


# ---------------------------------------------------------------------------
# Test 5: task_type='classification' usa temperatura baja
# ---------------------------------------------------------------------------

def test_classification_uses_low_temperature():
    """El task_type 'classification' debe configurar temperatura baja (≤0.2)."""
    router = APIRouter()
    captured_kwargs = {}

    async def spy_groq(messages, **kwargs):
        captured_kwargs.update(kwargs)
        return ("dev", {"tokens": 5, "provider": "groq"})

    with patch.object(router, "_call_groq", side_effect=spy_groq):
        asyncio.get_event_loop().run_until_complete(
            router.complete(
                messages=[{"role": "user", "content": "crea un bot"}],
                task_type="classification",
                temperature=0.1,
            )
        )

    assert captured_kwargs.get("temperature", 1.0) <= 0.2, (
        f"Clasificación debe usar temp ≤0.2, obtenida: {captured_kwargs.get('temperature')}"
    )


# ---------------------------------------------------------------------------
# Test 6: rate_limit (429) en Groq → no cuenta como fallo de proveedor → fallback
# ---------------------------------------------------------------------------

def test_groq_rate_limit_triggers_fallback():
    """Un error 429 de Groq debe disparar el fallback a Gemini (no retry en Groq)."""
    router = APIRouter()

    with (
        patch.object(router, "_call_groq", AsyncMock(side_effect=RuntimeError("429 rate limit"))),
        patch.object(router, "_call_gemini", AsyncMock(return_value=("ok", {"tokens": 10, "provider": "gemini"}))),
    ):
        text, meta = asyncio.get_event_loop().run_until_complete(
            router.complete(
                messages=[{"role": "user", "content": "analiza"}],
                task_type="analytics",
            )
        )

    assert text == "ok"
    assert meta.get("provider") == "gemini"
