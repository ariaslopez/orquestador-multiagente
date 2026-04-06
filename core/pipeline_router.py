"""PipelineRouter — Ejecuta pipelines en modo secuencial o paralelo+secuencial."""
from __future__ import annotations
import asyncio
import logging
from typing import List
from .base_agent import BaseAgent
from .context import AgentContext

logger = logging.getLogger(__name__)


class PipelineRouter:
    """
    Ejecuta agentes en el orden y modo correcto según el pipeline.

    Modos:
    - sequential: agentes uno tras otro, cada uno recibe el ctx del anterior
    - parallel_then_sequential: primeros agentes corren en paralelo,
      luego los siguientes en secuencia con los resultados combinados
    """

    async def run_sequential(
        self,
        agents: List[BaseAgent],
        ctx: AgentContext,
        max_retries: int = 3,
    ) -> AgentContext:
        """Ejecuta agentes en secuencia. Si uno falla más de max_retries, continúa."""
        for agent in agents:
            ctx.current_agent = agent.name
            logger.info(f"Pipeline [{ctx.pipeline_name}] → {agent.name}")
            ctx = await agent.execute(ctx)

            # Si el agente falló demasiadas veces, registrar y continuar
            if agent.name in ctx.failed_agents:
                retries = ctx.retry_counts.get(agent.name, 0)
                if retries >= max_retries:
                    logger.error(f"{agent.name} superó max_retries ({max_retries}), saltando")
                    continue

        return ctx

    async def run_parallel_then_sequential(
        self,
        parallel_agents: List[BaseAgent],
        sequential_agents: List[BaseAgent],
        ctx: AgentContext,
    ) -> AgentContext:
        """
        1. Corre los agentes paralelos al mismo tiempo (cada uno recibe una copia del ctx)
        2. Combina sus resultados en el ctx principal
        3. Continúa con los agentes secuenciales
        """
        logger.info(f"Pipeline [{ctx.pipeline_name}] → paralelo: {[a.name for a in parallel_agents]}")

        # Crear copias del ctx para cada agente paralelo
        import copy
        parallel_tasks = [
            agent.execute(copy.deepcopy(ctx))
            for agent in parallel_agents
        ]

        # Ejecutar todos en paralelo
        parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

        # Combinar resultados en el ctx principal
        for i, result in enumerate(parallel_results):
            if isinstance(result, Exception):
                agent_name = parallel_agents[i].name
                ctx.mark_agent_failed(agent_name, str(result))
                logger.error(f"Agente paralelo {agent_name} falló: {result}")
            else:
                # Merge de datos del ctx paralelo al principal
                for key, value in result.data.items():
                    ctx.data[f"{parallel_agents[i].name}_{key}"] = value
                ctx.completed_agents.extend([
                    a for a in result.completed_agents
                    if a not in ctx.completed_agents
                ])
                ctx.add_tokens(result.total_tokens, result.estimated_cost_usd)

        # Continuar con agentes secuenciales
        logger.info(f"Pipeline [{ctx.pipeline_name}] → secuencial: {[a.name for a in sequential_agents]}")
        ctx = await self.run_sequential(sequential_agents, ctx)

        return ctx
