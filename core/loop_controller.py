"""
Loop Controller — Fase 12
Motor de corrección autónoma del sistema CLAW.

Orquesta el ciclo completo de una tarea:
  1. Recibe un TaskPacket
  2. Ejecuta el pipeline del Maestro
  3. Si hay error: clasifica, inyecta contexto, reintenta
  4. Máximo MAX_ITERATIONS intentos antes de escalar
  5. Emite LaneEvents para el dashboard en cada paso

Interacción con hooks:
  Los hooks (stop_enforcer, posttool_validate) trabajan en paralelo
  con el loop. El loop maneja la lógica de alto nivel (clasificar errores,
  decidir recovery); los hooks manejan la lógica a nivel de herramienta.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, Callable, Awaitable

from .task_packet import TaskPacket, ExecutionMode, EffortLevel, EscalationPolicy
from infrastructure.worker_lifecycle import WorkerLifecycle, WorkerState, FailureKind, classify_error
from infrastructure.lane_events import LaneEvent, LaneEventType, lane_bus

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5


# Tipo del runner de pipeline: async callable que toma (TaskPacket, contexto) -> resultado
PipelineRunner = Callable[[TaskPacket, dict], Awaitable[dict]]


class LoopResult:
    """Resultado de la ejecución del loop."""
    def __init__(self, success: bool, output: dict, iterations: int,
                 final_error: str = "", worker: WorkerLifecycle = None):
        self.success     = success
        self.output      = output
        self.iterations  = iterations
        self.final_error = final_error
        self.worker      = worker

    def __repr__(self):
        status = "✅ OK" if self.success else "❌ FAIL"
        return f"LoopResult[{status} | iter={self.iterations} | error={self.final_error[:60]}]"


class LoopController:
    """
    Controlador de loop de corrección autónoma.

    Uso:
        controller = LoopController(pipeline_runner=maestro.run)
        result = await controller.run(task_packet)
        if result.success:
            print(result.output)
        else:
            print(f"Falló en {result.iterations} intentos: {result.final_error}")
    """

    def __init__(self,
                 pipeline_runner: PipelineRunner,
                 max_iterations:  int = MAX_ITERATIONS,
                 on_plan_ready:   Optional[Callable[[str], Awaitable[bool]]] = None):
        """
        Args:
            pipeline_runner:  Función async que ejecuta el pipeline (Maestro.run)
            max_iterations:   Máximo de intentos de corrección
            on_plan_ready:    Callback async para mostrar plan al usuario y esperar aprobación.
                              Recibe el plan como string, retorna True si aprobado.
        """
        self.pipeline_runner = pipeline_runner
        self.max_iterations  = max_iterations
        self.on_plan_ready   = on_plan_ready

    async def run(self, packet: TaskPacket) -> LoopResult:
        """
        Ejecuta el loop completo de una tarea.

        Flujo:
          PLAN_ONLY  -> generar plan -> mostrar al usuario -> retornar
          SUPERVISED -> [plan] -> [aprobar] -> ejecutar con confirmaciones
          AUTONOMOUS -> ejecutar sin interrupciones -> corregir si falla
        """
        worker = WorkerLifecycle(
            agent_name=f"loop_controller:{packet.pipeline}",
            max_recovery_attempts=self.max_iterations,
            on_state_change=self._on_state_change,
        )

        lane_bus.emit(LaneEvent.started(
            "loop_controller",
            f"Iniciando pipeline '{packet.pipeline}' | mode={packet.execution_mode.value} | effort={packet.effort.value}",
            session_id=packet.session_id,
            pipeline=packet.pipeline,
        ))

        worker.transition(WorkerState.READY)

        # --- FASE DE PLAN ---
        if packet.execution_mode in (ExecutionMode.PLAN_ONLY, ExecutionMode.SUPERVISED):
            plan_result = await self._generate_plan(packet, worker)
            if not plan_result.get("approved", True):
                return LoopResult(False, plan_result, 0, "Plan rechazado por el usuario", worker)
            if packet.is_plan_only:
                return LoopResult(True, plan_result, 0, worker=worker)

        # --- LOOP DE EJECUCIÓN Y CORRECCIÓN ---
        context    = {"packet": packet.to_dict(), "iteration": 0}
        last_error = ""

        for iteration in range(1, self.max_iterations + 1):
            context["iteration"] = iteration
            worker.transition(WorkerState.RUNNING)

            lane_bus.emit(LaneEvent.running(
                "loop_controller",
                f"Iteración {iteration}/{self.max_iterations}",
                iteration=iteration,
                pipeline=packet.pipeline,
            ))

            try:
                result = await self.pipeline_runner(packet, context)

                if result.get("success", True):
                    worker.transition(WorkerState.FINISHED)
                    lane_bus.emit(LaneEvent.green(
                        "loop_controller",
                        f"Pipeline completado en {iteration} iteración(es)",
                        pipeline=packet.pipeline,
                    ))
                    return LoopResult(True, result, iteration, worker=worker)

                # Pipeline retornó success=False: tratar como error recuperable
                error_msg = result.get("error", "Pipeline retornó fallo sin detalle")
                raise RuntimeError(error_msg)

            except Exception as exc:
                last_error      = str(exc)
                failure_kind    = classify_error(exc)
                error_context   = self._build_error_context(exc, failure_kind, context)

                worker.transition(WorkerState.FAILED, failure_kind, last_error[:200])

                lane_bus.emit(LaneEvent.red(
                    "loop_controller",
                    f"[{failure_kind.value}] {last_error[:150]}",
                    iteration=iteration,
                    metadata={"failure_kind": failure_kind.value, "error": last_error[:300]},
                    pipeline=packet.pipeline,
                ))

                if not worker.can_recover():
                    break

                # Inyectar contexto del error en el próximo intento
                context["last_error"]       = last_error
                context["last_error_kind"]  = failure_kind.value
                context["error_context"]    = error_context

                worker.recover()

                lane_bus.emit(LaneEvent.recovered(
                    "loop_controller",
                    iteration,
                    pipeline=packet.pipeline,
                ))

                # Back-off exponencial breve entre intentos
                await asyncio.sleep(min(2 ** (iteration - 1), 8))

        # Agotar intentos
        worker.abort(f"Máximo de iteraciones ({self.max_iterations}) alcanzado")
        lane_bus.emit(LaneEvent.failed(
            "loop_controller",
            f"Agotados {self.max_iterations} intentos. Último error: {last_error[:200]}",
            pipeline=packet.pipeline,
        ))

        await self._handle_escalation(packet, last_error)

        return LoopResult(False, {}, self.max_iterations, last_error, worker)

    # --- Métodos internos ---

    async def _generate_plan(self, packet: TaskPacket, worker: WorkerLifecycle) -> dict:
        """Genera un plan estructurado y opcionalmente espera aprobación."""
        worker.transition(WorkerState.RUNNING)

        lane_bus.emit(LaneEvent.plan_ready(
            f"Generando plan para: {packet.objective[:80]}...",
            pipeline=packet.pipeline,
        ))

        try:
            # Ejecutar pipeline en modo PLAN_ONLY para generar el plan
            plan_packet = TaskPacket(
                objective=packet.objective,
                pipeline=packet.pipeline,
                execution_mode=ExecutionMode.PLAN_ONLY,
                effort=packet.effort,
                context_files=packet.context_files,
                scope=packet.scope,
                session_id=packet.session_id,
            )
            result = await self.pipeline_runner(plan_packet, {"mode": "plan"})
            plan_text = result.get("plan", result.get("output", "Plan generado"))

        except Exception as e:
            plan_text = f"Error generando plan: {e}"
            logger.warning(f"Error en fase de plan: {e}")

        approved = True
        if self.on_plan_ready and not packet.is_autonomous:
            approved = await self.on_plan_ready(plan_text)

        if approved:
            lane_bus.emit(LaneEvent.approved(pipeline=packet.pipeline))

        return {"plan": plan_text, "approved": approved}

    def _build_error_context(self, exc: Exception, kind: FailureKind, context: dict) -> str:
        """
        Construye el contexto del error para inyectar al siguiente intento.
        El contexto se adapta según el tipo de error.
        """
        base = f"Error en iteración {context.get('iteration', '?')}: {str(exc)[:500]}"

        if kind == FailureKind.COMPILE:
            return (
                f"{base}\n\n"
                "INSTRUCCIÓN: Hay un error de sintaxis o importación. "
                "Revisa el código generado, corrige el error y vuelve a intentarlo. "
                "No cambies la lógica, solo corrige el error de código."
            )
        elif kind == FailureKind.TEST:
            return (
                f"{base}\n\n"
                "INSTRUCCIÓN: Los tests fallaron. "
                "Revisa qué assertions fallan y corrige la implementación para que pasen. "
                "No modifiques los tests, solo la implementación."
            )
        elif kind == FailureKind.PROVIDER:
            return (
                f"{base}\n\n"
                "INSTRUCCIÓN: El proveedor de LLM falló. "
                "El sistema intentará con el proveedor de fallback automáticamente."
            )
        elif kind == FailureKind.TIMEOUT:
            return (
                f"{base}\n\n"
                "INSTRUCCIÓN: La tarea tomó demasiado tiempo. "
                "Divide la tarea en pasos más pequeños."
            )
        else:
            return f"{base}\n\nINSTRUCCIÓN: Revisa el error y corrigió el problema antes de reintentar."

    async def _handle_escalation(self, packet: TaskPacket, error: str) -> None:
        """Maneja la política de escalamiento cuando se agotan los intentos."""
        policy = packet.escalation_policy
        if policy == EscalationPolicy.NOTIFY:
            logger.error(
                f"ESCALAMIENTO [{packet.task_id}]: {packet.pipeline} falló "
                f"después de {self.max_iterations} intentos.\n"
                f"Error final: {error[:300]}"
            )
        elif policy == EscalationPolicy.ABORT:
            raise RuntimeError(f"Pipeline '{packet.pipeline}' abortado: {error[:200]}")
        # SKIP: no hacer nada, continuar silenciosamente

    def _on_state_change(self, agent: str, prev: WorkerState, new: WorkerState) -> None:
        """Callback de cambio de estado para logging."""
        logger.debug(f"[{agent}] {prev.value} -> {new.value}")
