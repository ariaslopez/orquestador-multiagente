"""BaseAgent — Contrato base que todos los agentes deben implementar.

Cambios v2.2.1 (fix audit):
  - Bug A: eliminado double retry interno. execute() ya no tiene loop
    propio de reintentos — el PipelineRouter es el único responsable
    de reintentar agentes fallidos. Evita hasta 9 intentos silenciosos.
  - Bug B: _api_router singleton protegido con asyncio.Lock para evitar
    race condition en run_parallel_then_sequential (asyncio.gather).
  - Bug C: llm() usa el provider real post-fallback para calcular costo,
    no el provider que se hubiera elegido sin fallos.
"""
from __future__ import annotations
import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from .context import AgentContext

logger = logging.getLogger(__name__)

# Timeout global para llamadas LLM — configurable via .env
_LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT_SECONDS", "45"))

# Lock global para inicialización thread-safe del singleton APIRouter
_ROUTER_INIT_LOCK = asyncio.Lock()


class BaseAgent(ABC):
    """
    Clase base para todos los agentes del sistema CLAW.

    Cada agente recibe un AgentContext, lo enriquece con su trabajo
    y lo retorna para que el siguiente agente del pipeline lo use.

    Subclases deben definir:
      - name: str          (atributo de clase)
      - description: str   (atributo de clase)
      - async run(ctx)     (lógica del agente)

    IMPORTANTE sobre reintentos:
      BaseAgent.execute() NO hace reintentos propios.
      El PipelineRouter.run_sequential() es el único responsable
      de reintentar agentes fallidos (evita double retry silencioso).
    """

    name: str        = "BaseAgent"
    description: str = ""

    # APIRouter lazy — singleton compartido, protegido con Lock
    _api_router  = None
    _audit_logger = None

    @abstractmethod
    async def run(self, ctx: AgentContext) -> AgentContext:
        pass

    @classmethod
    async def _get_router(cls):
        """
        Inicializa el APIRouter de forma thread-safe.
        El Lock previene race condition cuando varios agentes
        del pipeline paralelo intentan inicializarlo al mismo tiempo.
        """
        if cls._api_router is None:
            async with _ROUTER_INIT_LOCK:
                # Double-check dentro del lock
                if cls._api_router is None:
                    from .api_router import APIRouter
                    cls._api_router = APIRouter()
        return cls._api_router

    async def llm(
        self,
        ctx: AgentContext,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Helper para llamar al LLM desde cualquier agente.

        - Infiere task_type desde el nombre del agente.
        - Aplica timeout configurable (LLM_TIMEOUT_SECONDS, default 45s).
        - Usa el provider REAL post-fallback para calcular el costo.
        - Actualiza métricas de tokens y costo en el contexto.
        - Lee ctx.data['effort'] para ajustar max_tokens si effort='min'.
        """
        router = await self._get_router()

        # Inferir task_type desde nombre del agente
        name_lower = self.name.lower()
        if any(k in name_lower for k in ("planner", "architect")):
            task_type = "planning"
        elif any(k in name_lower for k in ("coder", "developer")):
            task_type = "coding"
        elif any(k in name_lower for k in ("review", "qa", "security")):
            task_type = "review"
        elif any(k in name_lower for k in ("analyst", "research", "thesis", "data")):
            task_type = "analysis"
        elif any(k in name_lower for k in ("content", "writer")):
            task_type = "content"
        elif any(k in name_lower for k in ("summary", "format", "extract")):
            task_type = "formatting"
        else:
            task_type = "reasoning"

        # Ajustar max_tokens según effort
        effort = ctx.get_data("effort", "normal")
        if effort == "min":
            max_tokens = min(max_tokens, 1024)
        elif effort == "max":
            max_tokens = max(max_tokens, 8192)

        # Inyectar contexto de error si el agente está siendo reintentado
        last_error = ctx.get_data("_last_error")
        recovery_hint = ctx.get_data("_recovery_hint")
        if last_error and ctx.get_data("_last_failed_agent") == self.name:
            recovery_block = (
                f"\n\n--- CONTEXTO DE REINTENTO ---\n"
                f"Intento anterior falló con: {last_error[:300]}\n"
            )
            if recovery_hint:
                recovery_block += f"Hint de recuperación: {recovery_hint}\n"
            recovery_block += "--- FIN CONTEXTO ---\n"
            prompt = prompt + recovery_block

        messages = [{"role": "user", "content": prompt}]

        try:
            # complete() retorna (text, tokens, provider_used)
            text, tokens, provider_used = await asyncio.wait_for(
                router.complete(
                    messages=messages,
                    task_type=task_type,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
                timeout=_LLM_TIMEOUT,
            )
        except asyncio.TimeoutError:
            provider_used = router.select_provider(task_type)
            raise RuntimeError(
                f"[{self.name}] LLM timeout después de {_LLM_TIMEOUT}s "
                f"(provider={provider_used}, task_type={task_type}). "
                f"Ajusta LLM_TIMEOUT_SECONDS en .env si el modelo es lento."
            )

        # Bug C fix: usar provider_used REAL (post-fallback) para el costo
        cost = router.cost_for_tokens(tokens, provider_used)
        ctx.add_tokens(tokens, cost=cost, api=provider_used)

        return text

    def log(self, ctx: AgentContext, message: str) -> None:
        ctx.log(self.name, message)
        logging.getLogger(f"claw.agent.{self.name}").info(f"[{self.name}] {message}")

    def _get_audit_logger(self):
        if self._audit_logger is None:
            from infrastructure.audit_logger import AuditLogger
            BaseAgent._audit_logger = AuditLogger()
        return self._audit_logger

    async def execute(self, ctx: AgentContext) -> AgentContext:
        """
        Wrapper con logging, tracing automático y manejo de errores.

        DISEÑO DELIBERADO — sin reintentos propios:
          Este método ejecuta run() UNA sola vez y propaga la excepción
          si falla. El PipelineRouter.run_sequential() es quien decide
          si reintentar, cuántas veces, y con qué contexto de error.

          Razones:
            1. Evita double retry (antes: hasta 9 intentos silenciosos)
            2. El PipelineRouter tiene visibilidad del estado global
            3. El LoopController tiene visibilidad del pipeline completo
            4. Los logs son precisos: 'intento 2/3' significa exactamente eso
        """
        ctx.current_agent = self.name
        ctx.log(self.name, f"Iniciando {self.name}")
        logger.info(f"[{self.name}] Iniciando")

        tokens_before = ctx.total_tokens
        cost_before   = ctx.estimated_cost_usd
        start_time    = time.monotonic()
        trace_status  = "ok"

        try:
            ctx = await self.run(ctx)
            ctx.mark_agent_done(self.name)
            ctx.log(self.name, "✅ Completado exitosamente")
            logger.info(f"[{self.name}] ✅ Completado")

        except Exception as e:
            trace_status = "error"
            error_msg = str(e)
            ctx.mark_agent_failed(self.name, error_msg)
            ctx.log(self.name, f"💥 Error: {error_msg}")
            logger.error(f"[{self.name}] 💥 Error: {error_msg}")
            # Propagar la excepción para que PipelineRouter la maneje
            raise

        finally:
            # El tracing se registra siempre, incluso en error
            duration_ms = (time.monotonic() - start_time) * 1000
            tokens_used = max(ctx.total_tokens - tokens_before, 0)
            cost_used   = max(ctx.estimated_cost_usd - cost_before, 0.0)
            pipeline    = ctx.pipeline_name or ctx.task_type or "unknown"

            try:
                self._get_audit_logger().log_agent_trace(
                    agent_name=self.name,
                    pipeline=pipeline,
                    session_id=ctx.session_id,
                    duration_ms=duration_ms,
                    tokens=tokens_used,
                    cost_usd=cost_used,
                    status=trace_status,
                )
            except Exception:
                pass  # El tracing nunca debe romper el pipeline

        return ctx

    def __repr__(self) -> str:
        return f"<Agent: {self.name}>"
