"""RoadmapGeneratorAgent — genera roadmap visual con fases, milestones y metricas de exito."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class RoadmapGeneratorAgent(BaseAgent):
    name = "RoadmapGeneratorAgent"
    description = "Genera el roadmap del producto con fases, milestones y metricas de exito."

    async def run(self, context: AgentContext) -> AgentContext:
        requirements = context.get_data('requirements') or ''
        backlog = context.get_data('backlog') or ''
        sprints = context.get_data('sprints') or ''
        self.log(context, "Generando roadmap...")

        prompt = f"""Eres un Director de Producto con experiencia en startups SaaS.

REQUISITOS:
{requirements[:1000]}

BACKLOG RESUMIDO:
{backlog[:800]}

SPRINTS:
{sprints[:800]}

Genera el documento de proyecto completo:

# PLAN DE PROYECTO COMPLETO

## VISION Y OBJETIVOS
- Vision de producto
- OKRs del proyecto (2-3 Objectives con 2-3 KRs cada uno)

## ROADMAP POR FASES

### FASE 1 — MVP (Mes 1)
- Alcance
- Entregables
- Criterio de exito
- Recursos necesarios

### FASE 2 — CORE (Mes 2-3)
(mismo formato)

### FASE 3 — ESCALA (Mes 4+)
(mismo formato)

## MATRIZ DE RIESGOS
| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|

## PRESUPUESTO ESTIMADO
(horas de desarrollo por fase, asumiendo tarifa $50/hora)

## METRICAS DE EXITO DEL PROYECTO
- KPIs tecnicos (uptime, performance, cobertura de tests)
- KPIs de negocio (usuarios, conversion, revenue)
- Criterio de pivote vs perseverar

## PROXIMOS PASOS INMEDIATOS (esta semana)
1. ...
2. ...
3. ..."""

        result = await self.llm(context, prompt, temperature=0.3)
        context.final_output = result
        context.pipeline_name = "PM"
        self.log(context, "Roadmap generado — PM pipeline completado")
        return context
