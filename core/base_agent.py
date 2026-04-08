"""BaseAgent — Contrato base que todos los agentes deben implementar.

Cambios v2.2.2 (PR-1 — MCPHub + memoria):
  - _before_run(): recupera contexto de memoria episódica (mcp_memory)
    antes de ejecutar run(). Inyecta `memory_context` en ctx.data.
  - _after_run(): guarda el output relevante en mcp_memory después de run().
  - mcp_call(): helper directo al ctx.mcp_call() — self.mcp_call(ctx, ...)
  - Ambos hooks son NO-OP si ctx._mcp_hub no está inyectado (retrocompat).

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
from typing import Any, Dict, Optional, Tuple
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

    Hooks de memoria (v2.2.2):
      _before_run(): recupera memoria episódica antes de run()
      _after_run():  guarda resultado en memoria después de run()
      Ambos son NO-OP si MCPHub no está inyectado en el contexto.
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

    # ------------------------------------------------------------------
    # Hooks de memoria episódica (v2.2.2)
    # ------------------------------------------------------------------

    async def _before_run(self, ctx: AgentContext) -> None:
        """
        Hook pre-ejecución: recupera contexto de memoria episódica.

        Si mcp_memory está disponible, busca sesiones anteriores del mismo
        task_type + nombre de agente y las inyecta en ctx.data['memory_context'].
        Es NO-OP si MCPHub no está inyectado o mcp_memory no está configurado.
        """
        if not ctx.is_mcp_available("mcp_memory"):
            return
        try:
            key = f"{ctx.task_type}:{self.name}:last"
            memory = await ctx.mcp_call("mcp_memory", "retrieve", {"key": key})
            if memory:
                existing = ctx.get_data("memory_context") or []
                if isinstance(existing, list):
                    existing.append({"agent": self.name, "memory": memory})
                    ctx.set_data("memory_context", existing)
                ctx.log(self.name, f"Memoria episódica recuperada (key={key})")
        except Exception as e:
            logger.debug(f"[{self.name}] _before_run memoria: {e}")

    async def _after_run(self, ctx: AgentContext) -> None:
        """
        Hook post-ejecución: guarda output relevante en memoria episódica.

        Almacena un resumen del output del agente para que sesiones futuras
        puedan beneficiarse del contexto acumulado.
        Es NO-OP si MCPHub no está inyectado o mcp_memory no está configurado.
        """
        if not ctx.is_mcp_available("mcp_memory"):
            return
        try:
            # Extraer el dato más relevante que este agente produjo
            output_key = f"{self.name.lower()}_output"
            agent_output = ctx.get_data(output_key) or ctx.final_output or ""
            if not agent_output:
                return
            # Guardar con key normalizada por task_type + agente
            key = f"{ctx.task_type}:{self.name}:last"
            summary = str(agent_output)[:500]  # límite para evitar ruido
            await ctx.mcp_call("mcp_memory", "store", {"key": key, "value": summary})
            ctx.log(self.name, f"Resultado guardado en memoria (key={key})")
        except Exception as e:
            logger.debug(f"[{self.name}] _after_run memoria: {e}")

    # ------------------------------------------------------------------
    # Helper MCP directo
    # ------------------------------------------------------------------

    async def mcp_call(
        self,
        ctx: AgentContext,
        server: str,
        tool: str,
        params: Dict[str, Any] = None,
    ) -> Any:
        """
        Helper para llamar MCPs desde un agente de forma concisa.

        Equivalente a ctx.mcp_call() pero con guard automático.

        Uso en un agente:
            results = await self.mcp_call(ctx, "brave_search", "search", {"query": q})
            plan    = await self.mcp_call(ctx, "sequential_thinking", "think", {...})
        """
        return await ctx.mcp_call(server, tool, params or {})

    # ------------------------------------------------------------------
    # LLM helper
    # ------------------------------------------------------------------

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
        Wrapper con logging, hooks de memoria, tracing automático y manejo de errores.

        Flujo v2.2.2:
          1. _before_run()  → recupera memoria episódica (NO-OP si sin MCPHub)
          2. run()          → lógica del agente
          3. _after_run()   → guarda resultado en memoria (NO-OP si sin MCPHub)
          4. tracing        → audit_logger siempre

        DISEÑO DELIBERADO — sin reintentos propios:
          Este método ejecuta run() UNA sola vez y propaga la excepción
          si falla. El PipelineRouter.run_sequential() es quien decide
          si reintentar, cuántas veces, y con qué contexto de error.
        """
        ctx.current_agent = self.name
        ctx.log(self.name, f"Iniciando {self.name}")
        logger.info(f"[{self.name}] Iniciando")

        tokens_before = ctx.total_tokens
        cost_before   = ctx.estimated_cost_usd
        start_time    = time.monotonic()
        trace_status  = "ok"

        try:
            # Hook pre-ejecución: recuperar memoria episódica
            await self._before_run(ctx)

            ctx = await self.run(ctx)
            ctx.mark_agent_done(self.name)
            ctx.log(self.name, "✅ Completado exitosamente")
            logger.info(f"[{self.name}] ✅ Completado")

            # Hook post-ejecución: guardar resultado en memoria
            await self._after_run(ctx)

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
