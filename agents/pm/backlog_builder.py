"""BacklogBuilderAgent — crea epicas, historias de usuario y criterios de aceptacion."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class BacklogBuilderAgent(BaseAgent):
    name = "BacklogBuilderAgent"
    description = "Construye el backlog completo: epicas, historias de usuario y criterios de aceptacion."

    async def run(self, context: AgentContext) -> AgentContext:
        requirements = context.get_data('requirements') or context.user_input
        self.log(context, "Construyendo backlog...")

        prompt = f"""Eres un Product Owner senior experto en metodologias agiles (Scrum/Kanban).

REQUISITOS:
{requirements[:3000]}

Crea el backlog completo del producto:

## EPICAS
(grupos de funcionalidad de alto nivel, 3-6 epicas)

### EPIC-001: [Nombre]
**Descripcion:** ...
**Valor de negocio:** ...
**Historias de usuario:**

| ID | Historia | Criterios de Aceptacion | Story Points | Prioridad |
|----|----------|------------------------|-------------|----------|
| US-001 | Como [usuario], quiero [accion] para [beneficio] | - Dado... Cuando... Entonces... | 3 | Alta |

(Repite para cada epic)

## BACKLOG PRIORIZADO TOTAL
(tabla con todas las historias ordenadas por prioridad)
| Rank | ID | Historia | Epic | SP | Prioridad |
|------|-----|---------|------|-----|----------|

## DEFINICION DE READY (DoR)
(criterios para que una historia pueda entrar a sprint)

## DEFINICION DE DONE (DoD)
(criterios para que una historia este completa)"""

        result = await self.llm(context, prompt, temperature=0.25)
        context.set_data('backlog', result)
        self.log(context, "Backlog construido")
        return context
