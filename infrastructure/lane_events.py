"""
Lane Events — Fase 12
Eventos tipados para el dashboard WebSocket y audit_logger.

Reemplaza los logs de texto plano con un sistema estructurado
que el dashboard puede consumir y renderizar por agente.
"""

from __future__ import annotations

import time
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Any


class LaneEventType(str, Enum):
    STARTED   = "started"    # agente inicia su tarea
    RUNNING   = "running"    # agente en progreso (heartbeat)
    BLOCKED   = "blocked"    # agente esperando recurso
    GREEN     = "green"      # paso exitoso (tests pasan, review aprueba)
    RED       = "red"        # paso fallido (tests fallan, review rechaza)
    RECOVERED = "recovered"  # recovery exitoso
    FAILED    = "failed"     # fallo irrecuperable
    FINISHED  = "finished"   # tarea completada
    PLAN      = "plan"       # Maestro publicó plan para aprobación
    APPROVED  = "approved"   # usuario aprobó el plan
    ABORTED   = "aborted"    # tarea cancelada


@dataclass
class LaneEvent:
    """
    Evento tipado emitido por agentes durante la ejecución.

    Uso:
        event = LaneEvent.started("coder_agent", "Escribiendo modelos de base de datos")
        await websocket.send_text(event.to_json())
    """
    event_type:  LaneEventType
    agent:       str
    message:     str
    session_id:  str            = ""
    pipeline:    str            = ""
    iteration:   int            = 0
    metadata:    dict           = field(default_factory=dict)
    timestamp:   float          = field(default_factory=time.time)

    # --- Constructores semánticos ---

    @classmethod
    def started(cls, agent: str, message: str = "", **kw) -> "LaneEvent":
        return cls(LaneEventType.STARTED, agent, message or f"{agent} iniciado", **kw)

    @classmethod
    def running(cls, agent: str, message: str = "", **kw) -> "LaneEvent":
        return cls(LaneEventType.RUNNING, agent, message, **kw)

    @classmethod
    def blocked(cls, agent: str, reason: str = "", **kw) -> "LaneEvent":
        return cls(LaneEventType.BLOCKED, agent, reason or "Esperando recurso...", **kw)

    @classmethod
    def green(cls, agent: str, message: str = "", **kw) -> "LaneEvent":
        return cls(LaneEventType.GREEN, agent, message or f"{agent} ✅ completado", **kw)

    @classmethod
    def red(cls, agent: str, error: str = "", **kw) -> "LaneEvent":
        return cls(LaneEventType.RED, agent, error or f"{agent} ❌ falló", **kw)

    @classmethod
    def recovered(cls, agent: str, attempt: int = 1, **kw) -> "LaneEvent":
        return cls(LaneEventType.RECOVERED, agent, f"Recovery #{attempt} iniciado", **kw)

    @classmethod
    def failed(cls, agent: str, reason: str = "", **kw) -> "LaneEvent":
        return cls(LaneEventType.FAILED, agent, reason or f"{agent} falló definitivamente", **kw)

    @classmethod
    def finished(cls, agent: str, message: str = "", **kw) -> "LaneEvent":
        return cls(LaneEventType.FINISHED, agent, message or f"{agent} terminado", **kw)

    @classmethod
    def plan_ready(cls, message: str, **kw) -> "LaneEvent":
        return cls(LaneEventType.PLAN, "maestro", message, **kw)

    @classmethod
    def approved(cls, **kw) -> "LaneEvent":
        return cls(LaneEventType.APPROVED, "user", "Plan aprobado", **kw)

    # --- Serialización ---

    def to_dict(self) -> dict:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "LaneEvent":
        data["event_type"] = LaneEventType(data["event_type"])
        return cls(**data)

    def __str__(self) -> str:
        ts = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        icon = {
            LaneEventType.STARTED:   "▶️",
            LaneEventType.RUNNING:   "🔄",
            LaneEventType.BLOCKED:   "⏸️",
            LaneEventType.GREEN:     "✅",
            LaneEventType.RED:       "❌",
            LaneEventType.RECOVERED: "🔄",
            LaneEventType.FAILED:    "🚨",
            LaneEventType.FINISHED:  "🏁",
            LaneEventType.PLAN:      "📝",
            LaneEventType.APPROVED:  "👍",
            LaneEventType.ABORTED:   "⛔",
        }.get(self.event_type, "")
        return f"[{ts}] {icon} [{self.agent}] {self.message}"


class LaneEventBus:
    """
    Bus de eventos en memoria para la sesión activa.
    Los subscribers reciben eventos en tiempo real (dashboard WebSocket).
    """

    def __init__(self):
        self._subscribers: list = []
        self._history:     list[LaneEvent] = []

    def subscribe(self, callback) -> None:
        """Registra un callback async o sync para recibir eventos."""
        self._subscribers.append(callback)

    def emit(self, event: LaneEvent) -> None:
        """Emite un evento a todos los subscribers y lo guarda en historial."""
        self._history.append(event)
        import asyncio
        for cb in self._subscribers:
            if asyncio.iscoroutinefunction(cb):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(cb(event))
                except RuntimeError:
                    pass
            else:
                try:
                    cb(event)
                except Exception as e:
                    pass

    def history(self, agent: str = None) -> list[LaneEvent]:
        if agent:
            return [e for e in self._history if e.agent == agent]
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()


# Instancia global del bus para la sesión activa
lane_bus = LaneEventBus()
