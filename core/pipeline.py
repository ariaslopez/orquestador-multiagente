"""Definición y ejecución de pipelines de agentes."""
import logging
from typing import List
from .base_agent import BaseAgent
from .context import AgentContext

logger = logging.getLogger(__name__)


class Pipeline:
    """
    Un pipeline define una secuencia ordenada de agentes.
    Los agentes se ejecutan en orden, compartiendo el mismo contexto.
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.agents: List[BaseAgent] = []

    def add_agent(self, agent: BaseAgent) -> "Pipeline":
        """Agrega un agente al pipeline (fluent interface)."""
        self.agents.append(agent)
        return self

    def execute(self, context: AgentContext) -> AgentContext:
        """Ejecuta todos los agentes en orden."""
        for agent in self.agents:
            if not agent.can_run(context):
                logger.info(f"Agente '{agent.name}' omitido (can_run=False)")
                continue
            try:
                logger.info(f"▶ Ejecutando agente: {agent.name}")
                context = agent.run(context)
                context.mark_agent_done(agent.name)
                logger.info(f"✓ Agente '{agent.name}' completado")
            except Exception as e:
                logger.error(f"✗ Error en agente '{agent.name}': {e}")
                context = agent.on_error(context, e)
                # Continúa con el siguiente agente en lugar de abortar
        return context
