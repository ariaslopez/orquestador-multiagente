"""
Task Packet — Fase 12
Tipo de dato central que reemplaza los strings planos en CLI y /api/task.

TaskPacket encapsula todo lo necesario para ejecutar una tarea:
  - El objetivo en lenguaje natural
  - El pipeline a usar
  - El modo de ejecución (PLAN / SUPERVISED / AUTONOMOUS)
  - El nivel de esfuerzo (min / normal / max)
  - La política de branches y tests de aceptación
  - La política de escalamiento ante fallos
"""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ExecutionMode(str, Enum):
    """
    Modo de ejecución del pipeline.

    PLAN_ONLY:
      El agente investiga el contexto y genera un plan estructurado.
      No modifica ningún archivo. El usuario puede revisar el plan
      antes de decidir si ejecutar.
      CLI: --plan

    SUPERVISED:
      Modo por defecto. El agente pregunta al usuario antes de cada
      acción destructiva (sobreescribir archivos, ejecutar comandos, etc.).
      CLI: (sin flags especiales)

    AUTONOMOUS:
      Bypass de confirmaciones. El agente trabaja de inicio a fin sin
      interrumpir al usuario. Ideal para tareas bien definidas donde
      se confía en el sistema.
      CLI: --auto
      Equivalente a: --dangerously-skip-permissions en Claude Code
    """
    PLAN_ONLY  = "plan"
    SUPERVISED = "supervised"
    AUTONOMOUS = "autonomous"


class EffortLevel(str, Enum):
    """
    Nivel de profundidad de investigación antes de actuar.

    MIN:
      Respuesta rápida, ahorra tokens. Ideal para tu Athlon 3000G + Ollama.
      Usa modelo pequeño, sin thinking extendido.

    NORMAL:
      Balance calidad/velocidad. Modelo estándar, thinking breve.

    MAX:
      Investigación profunda. Thinking extendido (/think en Ollama,
      chain-of-thought en Groq/Gemini). Para tareas críticas.
    """
    MIN    = "min"
    NORMAL = "normal"
    MAX    = "max"


class BranchPolicy(str, Enum):
    """Política de manejo de branches en el pipeline DEV."""
    MAIN_ONLY   = "main"     # trabaja directo en main (solo para prototipos)
    NEW_BRANCH  = "branch"   # crea branch nueva por tarea (recomendado)
    EXISTING    = "existing" # trabaja en la branch actual


class EscalationPolicy(str, Enum):
    """Qué hacer cuando el loop de corrección agota sus intentos."""
    NOTIFY  = "notify"   # notificar al usuario y detenerse
    SKIP    = "skip"     # marcar tarea como fallida y continuar con la siguiente
    ABORT   = "abort"    # detener todo el pipeline


@dataclass
class TaskPacket:
    """
    Paquete de tarea tipado para el sistema CLAW.

    Uso básico:
        packet = TaskPacket.from_cli(
            task="Crea una API REST para señales de trading",
            pipeline="dev",
            effort="max",
            mode="auto",
        )

    Uso avanzado:
        packet = TaskPacket(
            objective="Refactoriza el módulo de backtesting",
            pipeline="dev",
            execution_mode=ExecutionMode.AUTONOMOUS,
            effort=EffortLevel.MAX,
            acceptance_tests=["pytest tests/test_backtest.py"],
            branch_policy=BranchPolicy.NEW_BRANCH,
            escalation_policy=EscalationPolicy.NOTIFY,
        )
    """
    # Campos requeridos
    objective:  str
    pipeline:   str

    # Modo de ejecución
    execution_mode:     ExecutionMode  = ExecutionMode.SUPERVISED
    effort:             EffortLevel    = EffortLevel.NORMAL

    # Políticas
    branch_policy:      BranchPolicy   = BranchPolicy.NEW_BRANCH
    escalation_policy:  EscalationPolicy = EscalationPolicy.NOTIFY

    # Tests de aceptación que deben pasar para marcar la tarea como exitosa
    acceptance_tests:   list[str] = field(default_factory=list)

    # Archivos a inyectar en contexto (de @archivo en el prompt)
    context_files:      list[str] = field(default_factory=list)

    # Scope/descripción adicional para el agente
    scope:              str = ""

    # Metadatos autogenerados
    task_id:    str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: float = field(default_factory=time.time)
    session_id: str   = ""

    # --- Constructores ---

    @classmethod
    def from_cli(cls,
                 task:     str,
                 pipeline: str = "dev",
                 effort:   str = "normal",
                 mode:     str = "supervised",
                 files:    list[str] = None,
                 scope:    str = "") -> "TaskPacket":
        """Crea un TaskPacket desde los args del CLI."""
        return cls(
            objective=task,
            pipeline=pipeline,
            execution_mode=ExecutionMode(mode) if mode in ExecutionMode._value2member_map_ else ExecutionMode.SUPERVISED,
            effort=EffortLevel(effort) if effort in EffortLevel._value2member_map_ else EffortLevel.NORMAL,
            context_files=files or [],
            scope=scope,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "TaskPacket":
        """Deserializa desde dict (API /api/task)."""
        data = dict(data)
        if "execution_mode" in data:
            data["execution_mode"] = ExecutionMode(data["execution_mode"])
        if "effort" in data:
            data["effort"] = EffortLevel(data["effort"])
        if "branch_policy" in data:
            data["branch_policy"] = BranchPolicy(data["branch_policy"])
        if "escalation_policy" in data:
            data["escalation_policy"] = EscalationPolicy(data["escalation_policy"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> dict:
        """Serializa para API y logs."""
        return {
            "task_id":          self.task_id,
            "objective":        self.objective,
            "pipeline":         self.pipeline,
            "execution_mode":   self.execution_mode.value,
            "effort":           self.effort.value,
            "branch_policy":    self.branch_policy.value,
            "escalation_policy": self.escalation_policy.value,
            "acceptance_tests": self.acceptance_tests,
            "context_files":    self.context_files,
            "scope":            self.scope,
            "session_id":       self.session_id,
            "created_at":       self.created_at,
        }

    # --- Helpers ---

    @property
    def is_autonomous(self) -> bool:
        return self.execution_mode == ExecutionMode.AUTONOMOUS

    @property
    def is_plan_only(self) -> bool:
        return self.execution_mode == ExecutionMode.PLAN_ONLY

    @property
    def thinking_enabled(self) -> bool:
        """True si el effort level justifica activar chain-of-thought."""
        return self.effort in (EffortLevel.NORMAL, EffortLevel.MAX)

    @property
    def use_extended_thinking(self) -> bool:
        """True si debe usar thinking extendido (/think tag en Ollama)."""
        return self.effort == EffortLevel.MAX

    def __str__(self) -> str:
        return (
            f"TaskPacket[{self.task_id}] "
            f"pipeline={self.pipeline} "
            f"mode={self.execution_mode.value} "
            f"effort={self.effort.value}\n"
            f"  objective: {self.objective[:80]}"
        )
