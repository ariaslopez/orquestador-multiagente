"""
Smoke test — Fase 14: LoopController — loop de corrección y modos de ejecución

Cubre:
  - AUTONOMOUS: pipeline que falla N veces activa reintentos hasta max_iterations
  - AUTONOMOUS: pipeline que falla 1 vez y tiene éxito al segundo intento
  - PLAN_ONLY:  retorna sin ejecutar el pipeline_fn
  - SUPERVISED: fallo + confirm_fn=False → cancela sin llegar a max_iterations
  - Estado final del WorkerState tras cada escenario
  - Clasificación de fallos (COMPILE, PROVIDER, TEST, TIMEOUT, TOOL_RUNTIME, UNKNOWN)

No usa red ni LLM — todo via AsyncMock y pipeline_fn sintético.

Ejecutar:
    pytest tests/smoke/test_loop_controller_retry.py -v
"""
from __future__ import annotations
import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from core.loop_controller import LoopController, ExecutionMode, WorkerState, FailureKind
from core.context import AgentContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx(error: str = None) -> AgentContext:
    ctx = AgentContext(user_input="test")
    if error:
        ctx.error = error
        ctx.status = "failed"
    return ctx


def _failing_pipeline(times: int, *, raise_exception: bool = False):
    """
    Retorna un pipeline_fn async que falla `times` veces y luego tiene éxito.
    Si raise_exception=True, lanza Exception en vez de marcar ctx.status.
    """
    call_count = 0

    async def pipeline_fn(ctx: AgentContext) -> AgentContext:
        nonlocal call_count
        call_count += 1
        if call_count <= times:
            if raise_exception:
                raise RuntimeError(f"fallo simulado #{call_count}")
            ctx.status = "failed"
            ctx.error = f"fallo simulado #{call_count}"
            return ctx
        # Éxito a partir de la iteración times+1
        ctx.status = "completed"
        ctx.error = None
        return ctx

    return pipeline_fn


# ---------------------------------------------------------------------------
# Test 1: AUTONOMOUS — falla siempre → alcanza max_iterations
# ---------------------------------------------------------------------------

def test_autonomous_max_iterations_reached():
    """Pipeline que siempre falla debe agotar max_iterations y quedar en FAILED."""
    controller = LoopController(
        mode=ExecutionMode.AUTONOMOUS,
        max_iterations=3,
    )
    pipeline_fn = _failing_pipeline(times=99)  # siempre falla

    ctx = asyncio.get_event_loop().run_until_complete(
        controller.run(pipeline_fn, _ctx())
    )

    assert controller.state == WorkerState.FAILED
    assert controller._iteration == 3
    # El error debe estar presente en ctx
    assert ctx.error is not None


# ---------------------------------------------------------------------------
# Test 2: AUTONOMOUS — falla 1 vez, éxito en el segundo intento
# ---------------------------------------------------------------------------

def test_autonomous_recovers_on_second_attempt():
    """Pipeline que falla 1 vez debe recuperarse en el segundo intento."""
    controller = LoopController(
        mode=ExecutionMode.AUTONOMOUS,
        max_iterations=5,
    )
    pipeline_fn = _failing_pipeline(times=1)  # falla solo 1 vez

    ctx = asyncio.get_event_loop().run_until_complete(
        controller.run(pipeline_fn, _ctx())
    )

    assert controller.state == WorkerState.FINISHED
    assert controller._iteration == 2  # falló en iter 1, éxito en iter 2
    assert ctx.status == "completed"
    assert ctx.error is None


# ---------------------------------------------------------------------------
# Test 3: AUTONOMOUS — pipeline lanza excepción no capturada
# ---------------------------------------------------------------------------

def test_autonomous_handles_exception_and_retries():
    """Una excepción no capturada en el pipeline no debe romper el LoopController."""
    controller = LoopController(
        mode=ExecutionMode.AUTONOMOUS,
        max_iterations=2,
    )
    pipeline_fn = _failing_pipeline(times=1, raise_exception=True)

    ctx = asyncio.get_event_loop().run_until_complete(
        controller.run(pipeline_fn, _ctx())
    )

    # No debe propagar la excepción; debe quedar en FINISHED al segundo intento
    assert controller.state == WorkerState.FINISHED


# ---------------------------------------------------------------------------
# Test 4: PLAN_ONLY — no ejecuta el pipeline_fn
# ---------------------------------------------------------------------------

def test_plan_only_does_not_execute_pipeline():
    """PLAN_ONLY debe retornar inmediatamente sin llamar al pipeline_fn."""
    executed = []

    async def spy_pipeline(ctx: AgentContext) -> AgentContext:
        executed.append(True)
        return ctx

    controller = LoopController(mode=ExecutionMode.PLAN_ONLY)

    ctx = asyncio.get_event_loop().run_until_complete(
        controller.run(spy_pipeline, _ctx())
    )

    assert len(executed) == 0, "PLAN_ONLY no debe ejecutar el pipeline_fn"
    assert ctx.get_data("execution_mode") == "plan_only"


# ---------------------------------------------------------------------------
# Test 5: SUPERVISED — usuario cancela el reintento
# ---------------------------------------------------------------------------

def test_supervised_cancels_when_user_denies():
    """En modo SUPERVISED, si confirm_fn retorna False, el loop debe cancelarse."""
    confirm_never = AsyncMock(return_value=False)

    controller = LoopController(
        mode=ExecutionMode.SUPERVISED,
        max_iterations=5,
        confirm_fn=confirm_never,
    )
    pipeline_fn = _failing_pipeline(times=99)

    ctx = asyncio.get_event_loop().run_until_complete(
        controller.run(pipeline_fn, _ctx())
    )

    assert controller.state == WorkerState.FAILED
    assert controller._iteration == 1  # canceló después del primer fallo
    confirm_never.assert_called_once()  # se preguntó exactamente una vez


# ---------------------------------------------------------------------------
# Test 6: SUPERVISED — usuario acepta y el pipeline tiene éxito en el reintento
# ---------------------------------------------------------------------------

def test_supervised_retries_when_user_confirms():
    """En modo SUPERVISED, si confirm_fn retorna True, debe reintentar."""
    confirm_always = AsyncMock(return_value=True)

    controller = LoopController(
        mode=ExecutionMode.SUPERVISED,
        max_iterations=5,
        confirm_fn=confirm_always,
    )
    pipeline_fn = _failing_pipeline(times=1)

    ctx = asyncio.get_event_loop().run_until_complete(
        controller.run(pipeline_fn, _ctx())
    )

    assert controller.state == WorkerState.FINISHED
    assert ctx.status == "completed"


# ---------------------------------------------------------------------------
# Test 7: Clasificación de fallos (_classify_failure)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("error_text,expected_kind", [
    ("SyntaxError: invalid syntax",                FailureKind.COMPILE),
    ("IndentationError en línea 12",               FailureKind.COMPILE),
    ("AssertionError: test_login failed",          FailureKind.TEST),
    ("429 rate limit exceeded",                    FailureKind.PROVIDER),
    ("todos los providers fallaron",               FailureKind.PROVIDER),
    ("TimeoutError: timed out after 30s",          FailureKind.TIMEOUT),
    ("PermissionError: [Errno 13] sandbox",        FailureKind.TOOL_RUNTIME),
    ("FileNotFoundError: no such file",            FailureKind.TOOL_RUNTIME),
    ("algo completamente desconocido",             FailureKind.UNKNOWN),
])
def test_failure_classification(error_text, expected_kind):
    """_classify_failure debe mapear mensajes de error a FailureKind correcto."""
    controller = LoopController(mode=ExecutionMode.AUTONOMOUS)
    ctx = _ctx(error=error_text)
    kind = controller._classify_failure(ctx)
    assert kind == expected_kind, (
        f"Error: '{error_text}'\n"
        f"Esperado:  {expected_kind}\n"
        f"Detectado: {kind}"
    )


# ---------------------------------------------------------------------------
# Test 8: Recovery context injection
# ---------------------------------------------------------------------------

def test_recovery_context_is_injected():
    """_inject_recovery_context debe escribir '_recovery_hint' en ctx.data."""
    controller = LoopController(mode=ExecutionMode.AUTONOMOUS)
    controller._iteration = 1
    ctx = _ctx()

    ctx = controller._inject_recovery_context(ctx, FailureKind.COMPILE)

    assert "_recovery_hint" in ctx.data
    assert "_failure_kind" in ctx.data
    assert ctx.data["_failure_kind"] == "compile"
    assert len(ctx.data["_recovery_hint"]) > 0
