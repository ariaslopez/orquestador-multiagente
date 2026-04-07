"""
Worker Lifecycle State Machine — Fase 12
Gestiona el ciclo de vida de cada agente con auto-recovery.

Estados:
  spawning -> ready -> running -> blocked -> failed -> finished

failure_kind:
  compile | test | tool_runtime | provider | timeout | unknown
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


class WorkerState(str, Enum):
    SPAWNING    = "spawning"    # inicializando, cargando contexto
    READY       = "ready"       # listo para recibir tarea
    RUNNING     = "running"     # ejecutando
    BLOCKED     = "blocked"     # esperando recurso externo (LLM, tool)
    FAILED      = "failed"      # error recuperable, intentando recovery
    FINISHED    = "finished"    # tarea completada exitosamente
    ABORTED     = "aborted"     # error irrecuperable, necesita intervención


class FailureKind(str, Enum):
    COMPILE      = "compile"       # SyntaxError, ImportError, NameError
    TEST         = "test"          # pytest / unittest fallan
    TOOL_RUNTIME = "tool_runtime"  # tool lanza excepción
    PROVIDER     = "provider"      # LLM no responde / rate limit
    TIMEOUT      = "timeout"       # tarea supera tiempo máximo
    UNKNOWN      = "unknown"       # error no clasificado


# Transiciones válidas: {estado_actual: [estados_destino_permitidos]}
VALID_TRANSITIONS: dict[WorkerState, list[WorkerState]] = {
    WorkerState.SPAWNING:  [WorkerState.READY, WorkerState.ABORTED],
    WorkerState.READY:     [WorkerState.RUNNING, WorkerState.ABORTED],
    WorkerState.RUNNING:   [WorkerState.BLOCKED, WorkerState.FAILED, WorkerState.FINISHED, WorkerState.ABORTED],
    WorkerState.BLOCKED:   [WorkerState.RUNNING, WorkerState.FAILED, WorkerState.ABORTED],
    WorkerState.FAILED:    [WorkerState.RUNNING, WorkerState.ABORTED],  # recovery -> RUNNING
    WorkerState.FINISHED:  [],  # estado terminal
    WorkerState.ABORTED:   [],  # estado terminal
}


@dataclass
class WorkerMetrics:
    started_at: float      = field(default_factory=time.time)
    finished_at: float     = 0.0
    state_changes: int     = 0
    recovery_attempts: int = 0
    tokens_used: int       = 0
    tool_calls: int        = 0

    @property
    def elapsed(self) -> float:
        end = self.finished_at if self.finished_at else time.time()
        return round(end - self.started_at, 2)


@dataclass
class WorkerLifecycle:
    """
    Gestiona el estado de un agente durante la ejecución de una tarea.

    Uso:
        worker = WorkerLifecycle(agent_name="coder_agent")
        worker.transition(WorkerState.RUNNING)
        # ... agente trabaja ...
        worker.transition(WorkerState.FAILED, FailureKind.TEST, "AssertionError en test_api.py")
        if worker.can_recover():
            worker.recover()  # reset a RUNNING para que loop_controller reintente
    """
    agent_name: str
    max_recovery_attempts: int = 2
    on_state_change: Optional[Callable[[str, WorkerState, WorkerState], None]] = None

    state: WorkerState  = field(default=WorkerState.SPAWNING, init=False)
    failure_kind: Optional[FailureKind] = field(default=None, init=False)
    failure_detail: str = field(default="", init=False)
    metrics: WorkerMetrics = field(default_factory=WorkerMetrics, init=False)

    def transition(self,
                   new_state: WorkerState,
                   failure_kind: Optional[FailureKind] = None,
                   detail: str = "") -> None:
        """Ejecuta una transición de estado validada."""
        allowed = VALID_TRANSITIONS.get(self.state, [])
        if new_state not in allowed:
            raise ValueError(
                f"[{self.agent_name}] Transición inválida: {self.state} -> {new_state}. "
                f"Permitidas: {[s.value for s in allowed]}"
            )

        prev_state = self.state
        self.state = new_state
        self.metrics.state_changes += 1

        if new_state in (WorkerState.FAILED, WorkerState.ABORTED):
            self.failure_kind = failure_kind or FailureKind.UNKNOWN
            self.failure_detail = detail
            logger.warning(f"[{self.agent_name}] {prev_state} -> {new_state} "
                           f"| {self.failure_kind.value}: {detail[:120]}")

        if new_state in (WorkerState.FINISHED, WorkerState.ABORTED):
            self.metrics.finished_at = time.time()

        logger.debug(f"[{self.agent_name}] {prev_state.value} -> {new_state.value}")

        if self.on_state_change:
            self.on_state_change(self.agent_name, prev_state, new_state)

    def can_recover(self) -> bool:
        """True si el agente puede intentar auto-recovery."""
        return (
            self.state == WorkerState.FAILED
            and self.metrics.recovery_attempts < self.max_recovery_attempts
            and self.failure_kind not in (FailureKind.PROVIDER,)  # provider falla -> escalar a fallback
        )

    def recover(self) -> None:
        """Intenta recovery: FAILED -> RUNNING."""
        if not self.can_recover():
            raise RuntimeError(f"[{self.agent_name}] No se puede recuperar. "
                               f"Intentos: {self.metrics.recovery_attempts}/{self.max_recovery_attempts}")
        self.metrics.recovery_attempts += 1
        self.failure_kind = None
        self.failure_detail = ""
        self.transition(WorkerState.RUNNING)
        logger.info(f"[{self.agent_name}] Recovery #{self.metrics.recovery_attempts} iniciado")

    def abort(self, reason: str = "") -> None:
        """Aborta el worker desde cualquier estado no terminal."""
        if self.state not in (WorkerState.FINISHED, WorkerState.ABORTED):
            self.transition(WorkerState.ABORTED, FailureKind.UNKNOWN, reason)

    def summary(self) -> dict:
        """Resumen del estado para logs y WebSocket."""
        return {
            "agent":            self.agent_name,
            "state":            self.state.value,
            "failure_kind":     self.failure_kind.value if self.failure_kind else None,
            "failure_detail":   self.failure_detail[:200],
            "recovery_attempts": self.metrics.recovery_attempts,
            "elapsed_s":        self.metrics.elapsed,
            "state_changes":    self.metrics.state_changes,
            "tokens_used":      self.metrics.tokens_used,
            "tool_calls":       self.metrics.tool_calls,
        }

    @property
    def is_terminal(self) -> bool:
        return self.state in (WorkerState.FINISHED, WorkerState.ABORTED)

    @property
    def is_healthy(self) -> bool:
        return self.state in (WorkerState.READY, WorkerState.RUNNING, WorkerState.BLOCKED)


def classify_error(error: Exception) -> FailureKind:
    """
    Clasifica una excepción en un FailureKind.
    Usado por loop_controller para decidir la estrategia de recovery.
    """
    err_type = type(error).__name__
    err_msg  = str(error).lower()

    if err_type in ("SyntaxError", "IndentationError", "ImportError", "ModuleNotFoundError", "NameError"):
        return FailureKind.COMPILE

    if err_type in ("AssertionError",) or "pytest" in err_msg or "assert" in err_msg or "test" in err_msg:
        return FailureKind.TEST

    if "timeout" in err_msg or "timed out" in err_msg or err_type == "TimeoutError":
        return FailureKind.TIMEOUT

    if any(x in err_msg for x in ("rate limit", "429", "quota", "api key", "unauthorized", "503")):
        return FailureKind.PROVIDER

    if err_type in ("FileNotFoundError", "PermissionError", "OSError", "IOError"):
        return FailureKind.TOOL_RUNTIME

    return FailureKind.UNKNOWN
