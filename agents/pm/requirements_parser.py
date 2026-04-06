"""RequirementsParserAgent — extrae y estructura requisitos funcionales y no funcionales."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class RequirementsParserAgent(BaseAgent):
    name = "RequirementsParserAgent"
    description = "Extrae requisitos funcionales y no funcionales de una descripcion en lenguaje natural."

    async def run(self, context: AgentContext) -> AgentContext:
        self.log(context, "Parseando requisitos...")

        prompt = f"""Eres un business analyst senior con experiencia en proyectos SaaS y sistemas distribuidos.

DESCRIPCION DEL PROYECTO:
{context.user_input}

Extrae y estructura todos los requisitos:

## VISION DEL PRODUCTO
- Problema que resuelve
- Usuario objetivo (persona)
- Propuesta de valor unica

## REQUISITOS FUNCIONALES
(lo que el sistema DEBE hacer)
| ID | Requisito | Prioridad (MoSCoW) | Criterio de Aceptacion |
|----|-----------|---------------------|------------------------|
| RF-001 | ... | Must Have | ... |

## REQUISITOS NO FUNCIONALES
| ID | Categoria | Requisito | Metrica |
|----|-----------|-----------|--------|
| RNF-001 | Performance | ... | ... |
(Categorias: Performance, Seguridad, Escalabilidad, Disponibilidad, UX, Mantenibilidad)

## RESTRICCIONES Y ASUNCIONES
- Restricciones tecnicas conocidas
- Asunciones del negocio
- Dependencias externas

## FUERA DE ALCANCE (v1)
(lo que explicitamente NO entra en la primera version)"""

        result = await self.llm(context, prompt, temperature=0.2)
        context.set_data('requirements', result)
        self.log(context, "Requisitos parseados")
        return context
