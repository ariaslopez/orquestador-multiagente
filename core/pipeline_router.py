"""PipelineRouter — Ejecuta pipelines en modo secuencial o paralelo+secuencial.

Cambios v2.2.0:
  - run_sequential: fix retry_counts (ahora se incrementa correctamente)
  - run_sequential: loop de corrección básico — inyecta error en ctx antes de reintentar
  - run_parallel_then_sequential: sin cambios en lógica, solo tipado mejorado
"""
from __future__ import annotations
import asyncio
import copy
import logging
import time
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
        max_retries: int = 2,
    ) -> AgentContext:
        """
        Ejecuta agentes en secuencia con loop de corrección.

        Por cada agente:
          1. Ejecuta el agente
          2. Si falla, incrementa retry_count (fix: antes nunca se incrementaba)
          3. Si retries < max_retries: inyecta el error en ctx y reintenta
          4. Si retries >= max_retries: loguea y continúa al siguiente agente

        El error se inyecta en ctx.data['_last_error'] para que el agente
        lo lea en el próximo intento y ajuste su comportamiento.
        """
        for agent in agents:
            ctx.current_agent = agent.name
            success = False

            while not success:
                retry_count = ctx.retry_counts.get(agent.name, 0)
                logger.info(
                    f"Pipeline [{ctx.pipeline_name}] → {agent.name} "
                    f"(intento {retry_count + 1}/{max_retries + 1})"
                )

                try:
                    ctx = await agent.execute(ctx)

                    # Si el agente ya marcó fallo internamente
                    if agent.name in ctx.failed_agents:
                        raise RuntimeError(
                            ctx.agent_logs.get(agent.name, ["Error desconocido"])[-1]
                        )

                    # Limpiar error previo si el agente tuvo éxito
                    ctx.data.pop("_last_error", None)
                    ctx.data.pop("_last_failed_agent", None)
                    success = True

                except Exception as e:
                    error_msg = str(e)
                    # Incrementar contador — FIX: antes nunca se incrementaba
                    new_count = ctx.increment_retry(agent.name)
                    ctx.mark_agent_failed(agent.name, error_msg)

                    if new_count >= max_retries:
                        logger.error(
                            f"{agent.name} superó max_retries ({max_retries}): {error_msg}"
                        )
                        # Limpiar de failed_agents para no bloquear el pipeline
                        # pero mantener el log del error
                        break
                    else:
                        logger.warning(
                            f"{agent.name} falló (intento {new_count}/{max_retries}): "
                            f"{error_msg[:120]} → reintentando con contexto de error"
                        )
                        # Inyectar contexto del error para que el agente lo use
                        # en el próximo intento (loop de corrección básico)
                        ctx.data["_last_error"] = error_msg
                        ctx.data["_last_failed_agent"] = agent.name
                        # Eliminar de failed_agents para permitir el reintento
                        if agent.name in ctx.failed_agents:
                            ctx.failed_agents.remove(agent.name)
                        # Pequeña pausa para evitar hammering
                        await asyncio.sleep(0.5)

        return ctx

    async def run_parallel_then_sequential(
        self,
        parallel_agents: List[BaseAgent],
        sequential_agents: List[BaseAgent],
        ctx: AgentContext,
    ) -> AgentContext:
        """
        1. Corre los agentes paralelos al mismo tiempo (cada uno recibe una copia del ctx)
        2. Combina sus resultados en el ctx principal (first-writer-wins)
        3. Continúa con los agentes secuenciales
        """
        parallel_names = [a.name for a in parallel_agents]
        logger.info(f"Pipeline [{ctx.pipeline_name}] → paralelo: {parallel_names}")

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

        for i, result in enumerate(parallel_results):
            agent_name = parallel_agents[i].name

            if isinstance(result, Exception):
                ctx.mark_agent_failed(agent_name, str(result))
                logger.error(f"Agente paralelo {agent_name} falló: {result}")
                continue

            # Merge de ctx.data — first-writer-wins (keys disjuntas entre paralelos)
            for key, value in result.data.items():
                if key not in ctx.data:
                    ctx.data[key] = value
                else:
                    logger.debug(
                        f"Merge paralelo: key '{key}' ya existe en ctx, "
                        f"ignorando valor de {agent_name}"
                    )

            for log_agent, entries in result.agent_logs.items():
                if log_agent not in ctx.agent_logs:
                    ctx.agent_logs[log_agent] = []
                ctx.agent_logs[log_agent].extend(entries)

            ctx.add_tokens(result.total_tokens, result.estimated_cost_usd)
            for api in result.apis_used:
                if api not in ctx.apis_used:
                    ctx.apis_used.append(api)

            if agent_name not in ctx.completed_agents:
                ctx.completed_agents.append(agent_name)

        sequential_names = [a.name for a in sequential_agents]
        logger.info(f"Pipeline [{ctx.pipeline_name}] → secuencial: {sequential_names}")
        return await self.run_sequential(sequential_agents, ctx)
