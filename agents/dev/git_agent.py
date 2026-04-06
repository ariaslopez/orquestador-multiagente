"""GitAgent — Hook opcional para integración con Git/GitHub.

Por ahora actúa como stub seguro: solo registra en logs que el proyecto
está listo para una posible sincronización con un repositorio remoto.
La lógica de PR automático se implementará en una fase posterior.
"""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class GitAgent(BaseAgent):
    name = "GitAgent"
    description = "Stub de integración Git: no realiza cambios, solo deja trazas en logs."

    async def run(self, context: AgentContext) -> AgentContext:
        repo = getattr(context, "git_repo", None)
        branch = getattr(context, "git_branch", "claw-auto")

        if not repo:
            self.log(context, "GitAgent: sin git_repo en el contexto, no se realizan acciones.")
            return context

        self.log(
            context,
            f"GitAgent: proyecto generado listo para integrarse con {repo}@{branch}. "
            f"(Implementación de PR automático pendiente)",
        )
        return context
