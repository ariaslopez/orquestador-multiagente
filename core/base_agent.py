"""BaseAgent — Contrato base que todos los agentes deben implementar."""
from __future__ import annotations
import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional
from .context import AgentContext

logger = logging.getLogger(__name__)

# Timeout global para llamadas LLM — configurable via .env
_LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT_SECONDS", "45"))


class BaseAgent(ABC):
    """
    Clase base para todos los agentes del sistema CLAW.

    Cada agente recibe un AgentContext, lo enriquece con su trabajo
    y lo retorna para que el siguiente agente del pipeline lo use.

    Subclases deben definir:
      - name: str          (atributo de clase)
      - description: str   (atributo de clase)
      - async run(ctx)     (lógica del agente)

    Opcionalmente:
      - max_retries: int   (default: 3)
    """

    name: str = "BaseAgent"
    description: str = ""
    max_retries: int = 3

    # APIRouter lazy — singleton compartido por todos los agentes
    _api_router = None
    # AuditLogger lazy — singleton compartido
    _audit_logger = None

    @abstractmethod
    async def run(self, ctx: AgentContext) -> AgentContext:
        pass

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
        - Actualiza métricas de tokens y costo en el contexto.
        """
        if self._api_router is None:
            from .api_router import APIRouter
            BaseAgent._api_router = APIRouter()

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

        messages = [{"role": "user", "content": prompt}]

        try:
            text, tokens = await asyncio.wait_for(
                self._api_router.complete(
                    messages=messages,
                    task_type=task_type,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
                timeout=_LLM_TIMEOUT,
            )
        except asyncio.TimeoutError:
            api_used = self._api_router.select_api(task_type)
            raise RuntimeError(
                f"[{self.name}] LLM timeout después de {_LLM_TIMEOUT}s "
                f"(api={api_used}, task_type={task_type}). "
                f"Ajusta LLM_TIMEOUT_SECONDS en .env si el modelo es lento."
            )

        api_used = self._api_router.select_api(task_type)
        cost = self._api_router.cost_for_tokens(tokens, api_used)
        ctx.add_tokens(tokens, cost=cost, api=api_used)

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
        Wrapper con manejo de errores, retries, logging y tracing automático.
        El PipelineRouter llama a este método, no a run() directamente.
        Captura tiempo de ejecución real y registra trace en audit_logger.
        """
        ctx.current_agent = self.name
        ctx.log(self.name, f"Iniciando {self.name}")
        logger.info(f"[{self.name}] Iniciando")

        tokens_before = getattr(ctx, 'total_tokens', 0)
        cost_before = getattr(ctx, 'estimated_cost_usd', 0.0)
        start_time = time.monotonic()

        attempts = 0
        last_error: Optional[Exception] = None
        max_retries = getattr(self.__class__, "max_retries", 3)
        trace_status = 'ok'

        while attempts < max_retries:
            try:
                attempts += 1
                ctx.log(self.name, f"Intento {attempts}/{max_retries}")
                ctx = await self.run(ctx)
                ctx.mark_agent_done(self.name)
                ctx.log(self.name, "✅ Completado exitosamente")
                logger.info(f"[{self.name}] ✅ Completado")
                break

            except Exception as e:
                last_error = e
                ctx.increment_retry(self.name)
                ctx.log(self.name, f"❌ Error (intento {attempts}): {str(e)}")
                logger.warning(f"[{self.name}] Error intento {attempts}: {e}")

                if attempts >= max_retries:
                    trace_status = 'error'
                    error_msg = str(last_error) if last_error else "Error desconocido"
                    ctx.mark_agent_failed(self.name, error_msg)
                    ctx.log(self.name, f"💥 Falló después de {max_retries} intentos: {error_msg}")
                    logger.error(f"[{self.name}] 💥 Falló: {error_msg}")
                    break

        # --- Tracing automático ---
        duration_ms = (time.monotonic() - start_time) * 1000
        tokens_used = getattr(ctx, 'total_tokens', 0) - tokens_before
        cost_used = getattr(ctx, 'estimated_cost_usd', 0.0) - cost_before
        pipeline = getattr(ctx, 'pipeline_name', '') or getattr(ctx, 'task_type', 'unknown')
        session_id = getattr(ctx, 'session_id', 'unknown')

        try:
            self._get_audit_logger().log_agent_trace(
                agent_name=self.name,
                pipeline=pipeline,
                session_id=session_id,
                duration_ms=duration_ms,
                tokens=max(tokens_used, 0),
                cost_usd=max(cost_used, 0.0),
                status=trace_status,
            )
        except Exception:
            pass  # El tracing nunca debe romper el pipeline

        return ctx

    def __repr__(self) -> str:
        return f"<Agent: {self.name}>"
