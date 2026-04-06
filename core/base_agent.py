"""BaseAgent — Contrato base que todos los agentes deben implementar."""
from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Optional
from .context import AgentContext

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Clase base para todos los agentes del sistema CLAW.

    Cada agente recibe un AgentContext, lo enriquece con su trabajo
    y lo retorna para que el siguiente agente del pipeline lo use.
    """

    def __init__(self, name: str, description: str = "", max_retries: int = 3):
        self.name = name
        self.description = description
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"claw.agent.{name}")

    @abstractmethod
    async def run(self, ctx: AgentContext) -> AgentContext:
        """
        Ejecuta la lógica del agente.

        Args:
            ctx: Contexto compartido con datos del pipeline

        Returns:
            ctx: Contexto actualizado con los resultados del agente
        """
        pass

    async def execute(self, ctx: AgentContext) -> AgentContext:
        """
        Wrapper con manejo de errores, retries y logging automático.
        El Maestro llama a este método, no a run() directamente.
        """
        ctx.current_agent = self.name
        ctx.log(self.name, f"Iniciando {self.name}")
        self.logger.info(f"[{self.name}] Iniciando")

        attempts = 0
        last_error: Optional[Exception] = None

        while attempts < self.max_retries:
            try:
                attempts += 1
                ctx.log(self.name, f"Intento {attempts}/{self.max_retries}")
                ctx = await self.run(ctx)
                ctx.mark_agent_done(self.name)
                ctx.log(self.name, f"✅ Completado exitosamente")
                self.logger.info(f"[{self.name}] ✅ Completado")
                return ctx

            except Exception as e:
                last_error = e
                retry_count = ctx.increment_retry(self.name)
                ctx.log(self.name, f"❌ Error (intento {attempts}): {str(e)}")
                self.logger.warning(f"[{self.name}] Error intento {attempts}: {e}")

                if attempts >= self.max_retries:
                    break

        # Todos los intentos fallaron
        error_msg = str(last_error) if last_error else "Error desconocido"
        ctx.mark_agent_failed(self.name, error_msg)
        ctx.log(self.name, f"💥 Falló después de {self.max_retries} intentos: {error_msg}")
        self.logger.error(f"[{self.name}] 💥 Falló: {error_msg}")
        return ctx

    def __repr__(self) -> str:
        return f"<Agent: {self.name}>"
