"""SprintPlannerAgent — prioriza con RICE/MoSCoW y arma sprints con capacidad real."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class SprintPlannerAgent(BaseAgent):
    name = "SprintPlannerAgent"
    description = "Prioriza el backlog con RICE y planifica sprints con velocidad y capacidad real."

    async def run(self, context: AgentContext) -> AgentContext:
        backlog = context.get_data('backlog') or ''
        requirements = context.get_data('requirements') or ''
        self.log(context, "Planificando sprints...")

        prompt = f"""Eres un Scrum Master y Agile Coach con 8 anos de experiencia.

BACKLOG:
{backlog[:2500]}

CONTEXTO DEL PROYECTO:
{requirements[:500]}

Planifica los sprints considerando:
- Equipo asumido: 2-3 desarrolladores
- Velocidad estimada: 20-30 story points por sprint de 2 semanas
- Objetivo: MVP funcional en Sprint 1-2

## SPRINT 1 (Semana 1-2) — OBJETIVO: [nombre del objetivo]
**Meta del Sprint:** ...
**Capacidad:** X story points
| Historia | SP | Responsable sugerido |
|----------|-----|---------------------|

**Total SP:** X / X capacidad

## SPRINT 2 (Semana 3-4) — OBJETIVO: [nombre]
(mismo formato)

## SPRINT 3 (Semana 5-6) — OBJETIVO: [nombre]
(mismo formato)

## SPRINTS FUTUROS (Semana 7+)
(descripcion de alcance sin detalle de tareas)

## MILESTONES CLAVE
| Milestone | Sprint | Entregable |
|-----------|--------|------------|

## RIESGOS DE PLANIFICACION
(lista con mitigacion)"""

        result = await self.llm(context, prompt, temperature=0.2)
        context.set_data('sprints', result)
        self.log(context, "Sprints planificados")
        return context
