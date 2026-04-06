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
        2. Combina sus resultados en el ctx principal — sin prefijo de nombre de agente
        3. Continúa con los agentes secuenciales
        """
        import copy
        import time

        parallel_names = [a.name for a in parallel_agents]
        logger.info(f"Pipeline [{ctx.pipeline_name}] → paralelo: {parallel_names}")

        # Cada agente paralelo recibe una copia independiente del ctx
        parallel_tasks = [
            agent.execute(copy.deepcopy(ctx))
            for agent in parallel_agents
        ]

        t0 = time.monotonic()
        parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
        elapsed = time.monotonic() - t0
        logger.info(
            f"Pipeline [{ctx.pipeline_name}] → paralelo completado en {elapsed:.2f}s"
        )

        # Combinar resultados en el ctx principal
        for i, result in enumerate(parallel_results):
            agent_name = parallel_agents[i].name

            if isinstance(result, Exception):
                ctx.mark_agent_failed(agent_name, str(result))
                logger.error(f"Agente paralelo {agent_name} falló: {result}")
                continue

            # Merge de ctx.data SIN prefijo de nombre de agente.
            # Estrategia "first writer wins": si la key ya existe no se pisa.
            # Es seguro porque los agentes paralelos escriben en keys disjuntas
            # (web_results / market_snapshot, market_historical, etc.).
            for key, value in result.data.items():
                if key not in ctx.data:
                    ctx.data[key] = value
                else:
                    logger.debug(
                        f"Merge paralelo: key '{key}' ya existe en ctx, "
                        f"ignorando valor de {agent_name}"
                    )

            # Merge de agent_logs (extend, no reemplazar)
            for log_agent, entries in result.agent_logs.items():
                if log_agent not in ctx.agent_logs:
                    ctx.agent_logs[log_agent] = []
                ctx.agent_logs[log_agent].extend(entries)

            # Merge de métricas acumuladas
            ctx.add_tokens(result.total_tokens, result.estimated_cost_usd)
            for api in result.apis_used:
                if api not in ctx.apis_used:
                    ctx.apis_used.append(api)

            # Registrar agente como completado
            if agent_name not in ctx.completed_agents:
                ctx.completed_agents.append(agent_name)

        # Continuar con agentes secuenciales (reciben ctx enriquecido por paralelos)
        sequential_names = [a.name for a in sequential_agents]
        logger.info(f"Pipeline [{ctx.pipeline_name}] → secuencial: {sequential_names}")
        ctx = await self.run_sequential(sequential_agents, ctx)

        return ctx
