"""LoopController — Autonomía y loop de corrección para el sistema CLAW.

Fase 12: Worker lifecycle state machine + ExecutionMode + loop autónomo.

Arquitectura:
  Maestro.run()
    → LoopController.run(pipeline_fn, ctx)
        → ExecutionMode.SUPERVISED  → pregunta antes de acciones destructivas
        → ExecutionMode.AUTONOMOUS  → ejecuta sin interrupciones
        → ExecutionMode.PLAN_ONLY   → genera plan, no modifica nada
        → loop interno: detecta errores → inyecta contexto → reintenta (max 5)

Estados del worker (WorkerState):
  spawning → ready → running → blocked → failed → finished

Integración con PipelineRouter:
  PipelineRouter.run_sequential() ya inyecta _last_error en ctx.
  LoopController usa ese contexto para decidir si reintentar el pipeline
  completo o solo el agente fallido.
"""
from __future__ import annotations
import asyncio
import logging
from enum import Enum, auto
from typing import Callable, Awaitable, Optional
from .context import AgentContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ExecutionMode(Enum):
    """Modo de ejecución del pipeline."""
    PLAN_ONLY   = "plan_only"    # Solo genera plan, no ejecuta ni modifica
    SUPERVISED  = "supervised"   # Pide confirmación antes de acciones destructivas
    AUTONOMOUS  = "autonomous"   # Ejecuta sin interrupciones hasta terminar


class WorkerState(Enum):
    """Estado del worker durante la ejecución del pipeline."""
    SPAWNING  = auto()  # Inicializando
    READY     = auto()  # Listo para recibir tarea
    RUNNING   = auto()  # Ejecutando agente
    BLOCKED   = auto()  # Esperando confirmación (modo SUPERVISED)
    FAILED    = auto()  # Error irrecuperable
    FINISHED  = auto()  # Completado exitosamente


class FailureKind(Enum):
    """Tipo de fallo para determinar estrategia de recuperación."""
    COMPILE      = "compile"       # Error de sintaxis/compilación
    TEST         = "test"          # Tests fallaron
    TOOL_RUNTIME = "tool_runtime"  # Error de herramienta (filesystem, git, etc.)
    PROVIDER     = "provider"      # Error de API/LLM
    TIMEOUT      = "timeout"       # Timeout de agente
    UNKNOWN      = "unknown"       # Error no clasificado


# ---------------------------------------------------------------------------
# LoopController
# ---------------------------------------------------------------------------

class LoopController:
    """
    Controlador de ejecución autónoma con loop de corrección.

    Uso:
        controller = LoopController(
            mode=ExecutionMode.SUPERVISED,
            max_iterations=5,
        )
        ctx = await controller.run(pipeline_fn, ctx)

    El pipeline_fn es un callable async que recibe y retorna AgentContext.
    En cada iteración, el controller:
      1. Ejecuta el pipeline
      2. Detecta el tipo de fallo (si lo hay)
      3. Inyecta contexto del error + estrategia de recuperación
      4. Reintenta si iterations < max_iterations
      5. Escala al usuario si mode=SUPERVISED y el fallo requiere intervención
    """

    MAX_ITERATIONS_DEFAULT = 5

    def __init__(
        self,
        mode: ExecutionMode = ExecutionMode.SUPERVISED,
        max_iterations: int = MAX_ITERATIONS_DEFAULT,
        confirm_fn: Optional[Callable[[str], Awaitable[bool]]] = None,
    ):
        """
        Args:
            mode: Modo de ejecución (SUPERVISED por defecto).
            max_iterations: Máximo de reintentos del loop de corrección.
            confirm_fn: Función async para pedir confirmación al usuario
                        en modo SUPERVISED. Si None, se usa input() bloqueante.
        """
        self.mode = mode
        self.max_iterations = max_iterations
        self.confirm_fn = confirm_fn or self._default_confirm
        self._state = WorkerState.SPAWNING
        self._iteration = 0

    @property
    def state(self) -> WorkerState:
        return self._state

    def _transition(self, new_state: WorkerState) -> None:
        logger.debug(f"WorkerState: {self._state.name} → {new_state.name}")
        self._state = new_state

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    async def run(
        self,
        pipeline_fn: Callable[[AgentContext], Awaitable[AgentContext]],
        ctx: AgentContext,
    ) -> AgentContext:
        """
        Ejecuta el pipeline con loop de corrección autónomo.

        Si mode=PLAN_ONLY, genera el plan y retorna sin ejecutar.
        Si mode=SUPERVISED o AUTONOMOUS, ejecuta con reintentos.
        """
        self._transition(WorkerState.READY)

        if self.mode == ExecutionMode.PLAN_ONLY:
            logger.info("LoopController: modo PLAN_ONLY — generando plan sin ejecutar")
            ctx.set_data("execution_mode", "plan_only")
            ctx.log("loop_controller", "Modo PLAN_ONLY: solo se genera el plan de acción")
            return ctx

        self._transition(WorkerState.RUNNING)
        ctx.set_data("execution_mode", self.mode.value)
        ctx.set_data("loop_max_iterations", self.max_iterations)

        while self._iteration < self.max_iterations:
            self._iteration += 1
            ctx.set_data("loop_iteration", self._iteration)
            logger.info(
                f"LoopController: iteración {self._iteration}/{self.max_iterations} "
                f"| mode={self.mode.value}"
            )

            try:
                ctx = await pipeline_fn(ctx)

                # Pipeline completado sin errores
                if ctx.status != "failed" and not ctx.error:
                    self._transition(WorkerState.FINISHED)
                    ctx.log(
                        "loop_controller",
                        f"Pipeline completado en {self._iteration} iteración(es)",
                    )
                    return ctx

                # Pipeline completó pero con errores en agentes
                failure_kind = self._classify_failure(ctx)
                logger.warning(
                    f"LoopController: pipeline terminó con errores "
                    f"({failure_kind.value}) en iteración {self._iteration}"
                )

            except Exception as e:
                failure_kind = self._classify_failure(ctx, str(e))
                ctx.error = str(e)
                logger.error(
                    f"LoopController: excepción en iteración {self._iteration}: {e}"
                )

            # ¿Podemos recuperarnos?
            if self._iteration >= self.max_iterations:
                logger.error(
                    f"LoopController: máximo de iteraciones ({self.max_iterations}) alcanzado"
                )
                self._transition(WorkerState.FAILED)
                break

            # Modo SUPERVISED: preguntar al usuario si continuar
            if self.mode == ExecutionMode.SUPERVISED:
                self._transition(WorkerState.BLOCKED)
                should_continue = await self.confirm_fn(
                    f"\n⚠️  Pipeline falló ({failure_kind.value}) en iteración "
                    f"{self._iteration}.\n¿Reintentar con contexto de error? [s/N]: "
                )
                if not should_continue:
                    logger.info("LoopController: usuario canceló el reintento")
                    self._transition(WorkerState.FAILED)
                    return ctx
                self._transition(WorkerState.RUNNING)

            # Inyectar contexto de recuperación antes del siguiente intento
            ctx = self._inject_recovery_context(ctx, failure_kind)
            # Resetear estado para el próximo intento
            ctx.status = "running"
            ctx.error = None
            ctx.failed_agents.clear()
            ctx.retry_counts.clear()

            # Backoff antes del reintento
            await asyncio.sleep(1.0)

        return ctx

    # ------------------------------------------------------------------
    # Clasificación de fallos
    # ------------------------------------------------------------------

    def _classify_failure(
        self, ctx: AgentContext, error_msg: str = ""
    ) -> FailureKind:
        """
        Determina el tipo de fallo para elegir la estrategia de recuperación.

        Analiza:
          - ctx.error (mensaje de error del pipeline)
          - ctx.failed_agents (agentes que fallaron)
          - error_msg (excepción no capturada)
        """
        text = (ctx.error or error_msg or "").lower()

        # Errores de compilación/sintaxis
        if any(kw in text for kw in [
            "syntaxerror", "indentationerror", "nameerror",
            "importerror", "modulenotfounderror", "syntax",
        ]):
            return FailureKind.COMPILE

        # Tests fallando
        if any(kw in text for kw in [
            "assertionerror", "test failed", "pytest", "failed",
            "assert", "expected", "test_",
        ]):
            return FailureKind.TEST

        # Error de provider/API
        if any(kw in text for kw in [
            "429", "rate limit", "quota", "provider", "api",
            "connection", "timeout", "todos los providers",
        ]):
            return FailureKind.PROVIDER

        # Timeout
        if "timeout" in text or "timed out" in text:
            return FailureKind.TIMEOUT

        # Error de herramienta
        if any(kw in text for kw in [
            "permissionerror", "filenotfounderror", "oserror",
            "git", "filesystem", "sandbox",
        ]):
            return FailureKind.TOOL_RUNTIME

        return FailureKind.UNKNOWN

    def _inject_recovery_context(
        self, ctx: AgentContext, failure_kind: FailureKind
    ) -> AgentContext:
        """
        Inyecta hints de recuperación en ctx.data para que los agentes
        lean en el próximo intento y ajusten su comportamiento.
        """
        recovery_hints = {
            FailureKind.COMPILE: (
                "El código generado tiene errores de sintaxis. "
                "Revisa indentación, imports y nombres de variables. "
                "Asegúrate de que el código sea Python válido."
            ),
            FailureKind.TEST: (
                "Los tests fallaron. Analiza el output del test, "
                "identifica qué función o clase falla y corrígela "
                "sin romper los tests que sí pasan."
            ),
            FailureKind.PROVIDER: (
                "El provider LLM no está disponible. "
                "Verifica OLLAMA_ENABLED, GROQ_API_KEY, GEMINI_API_KEY en .env. "
                "Si usas Ollama, asegúrate de que el servicio está corriendo."
            ),
            FailureKind.TOOL_RUNTIME: (
                "Una herramienta del sistema falló (filesystem, git, etc.). "
                "Verifica permisos de archivos y que el sandbox esté configurado "
                "correctamente. Revisa config.yaml sección 'security'."
            ),
            FailureKind.TIMEOUT: (
                "La tarea tomó demasiado tiempo. Divide la tarea en partes más "
                "pequeñas o usa --effort min para respuestas más rápidas."
            ),
            FailureKind.UNKNOWN: (
                "Error desconocido en el pipeline. "
                "Revisa los logs detallados con python main.py --history."
            ),
        }

        hint = recovery_hints.get(failure_kind, recovery_hints[FailureKind.UNKNOWN])
        ctx.set_data("_recovery_hint", hint)
        ctx.set_data("_failure_kind", failure_kind.value)
        ctx.set_data("_loop_iteration", self._iteration)
        ctx.log(
            "loop_controller",
            f"Iteración {self._iteration} falló ({failure_kind.value}): "
            f"inyectando hint de recuperación → reintentando",
        )
        return ctx

    # ------------------------------------------------------------------
    # Confirmación de usuario (modo SUPERVISED)
    # ------------------------------------------------------------------

    @staticmethod
    async def _default_confirm(prompt: str) -> bool:
        """Confirmación bloqueante en terminal. En producción, reemplazar por WebSocket."""
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, lambda: input(prompt).strip().lower()
        )
        return response in ("s", "si", "sí", "y", "yes", "1")
