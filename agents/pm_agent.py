"""PMAgent — Convierte descripcion de proyecto en backlog estructurado con sprints."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class PMAgent(BaseAgent):
    name = "PMAgent"
    description = "Genera backlog, roadmap y sprints desde una descripcion de proyecto."

    async def run(self, context: AgentContext) -> AgentContext:
        self.log(context, "Generando plan de proyecto (PM)...")
        prompt = f"""Eres un Project Manager senior experto en metodologias agiles.
Convierte la siguiente descripcion en un plan de proyecto completo:

DESCRIPCION:
{context.user_input}

Genera:
## VISION DEL PRODUCTO
(que problema resuelve y para quien)

## EPICS
(grupos grandes de funcionalidad, 3-5 epics)

## BACKLOG DE TAREAS
(lista priorizada con estimaciones en story points)
| # | Tarea | Epic | Story Points | Prioridad |
|---|-------|------|-------------|----------|

## SPRINT 1 (semana 1-2) — MVP
(tareas del primer sprint, las mas criticas)

## SPRINT 2 (semana 3-4)
(funcionalidades core)

## SPRINT 3+ (semana 5+)
(mejoras, optimizaciones, nice-to-haves)

## RIESGOS DEL PROYECTO
(lista de riesgos con probabilidad e impacto)

## DEFINICION DE DONE
(criterios para considerar el proyecto completo)"""
        plan = await self.llm(context, prompt, temperature=0.3)
        context.final_output = plan
        context.pipeline_name = "PM"
        self.log(context, "Plan PM generado")
        return context
