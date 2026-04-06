"""GitAgent — Hook opcional para integración con Git/GitHub.

Estado actual: stub seguro.
  - No realiza ninguna escritura en GitHub.
  - Registra en logs que el proyecto está listo para sincronización.
  - Verifica GITHUB_CONFIRM_BEFORE_PUSH como guard preventivo:
    cuando se implemente la lógica real de PR, DEBE respetar este flag.

Implementación de PR automático: ver ROADMAP.md (deuda técnica).
"""
from __future__ import annotations
import os
from core.base_agent import BaseAgent
from core.context import AgentContext


class GitAgent(BaseAgent):
    name = "GitAgent"
    description = "Stub de integración Git: no realiza cambios, solo deja trazas en logs."

    async def run(self, context: AgentContext) -> AgentContext:
        repo = context.get_data("git_repo") or getattr(context, "git_repo", None)
        branch = context.get_data("git_branch") or getattr(context, "git_branch", "claw-auto")

        if not repo:
            self.log(context, "GitAgent: sin git_repo en el contexto, no se realizan acciones.")
            return context

        # --- Guard preventivo: Ataque 2 (push autónomo sin supervisión) ---
        # Verificar GITHUB_CONFIRM_BEFORE_PUSH en runtime (no en import time).
        # Este check DEBE mantenerse cuando se implemente la lógica real de PR.
        confirm_before_push = os.environ.get(
            "GITHUB_CONFIRM_BEFORE_PUSH", "true"
        ).strip().lower()

        push_requires_confirmation = confirm_before_push not in ("false", "0", "no")

        if not push_requires_confirmation:
            # Si alguien desactivó la confirmación explicitamente,
            # loguearlo como SECURITY WARNING para que quede en auditoría.
            self.log(
                context,
                "⚠ SECURITY WARNING: GITHUB_CONFIRM_BEFORE_PUSH=false detectado. "
                "Cualquier push futuro a GitHub será automático sin confirmación. "
                "Considera restablecerlo a 'true' si no es intencional."
            )
            context.set_data("git_push_requires_confirmation", False)
        else:
            context.set_data("git_push_requires_confirmation", True)

        # Stub: registrar que el proyecto está listo para sincronización.
        # La implementación real del PR debe:
        #   1. Leer context.get_data('git_push_requires_confirmation')
        #   2. Si False → proceder con push (riesgo aceptado por el usuario)
        #   3. Si True → solicitar confirmación interactiva o abortar en modo auto
        self.log(
            context,
            f"GitAgent: proyecto generado listo para integrarse con {repo}@{branch}. "
            f"(confirm_before_push={push_requires_confirmation}) "
            f"Implementación de PR automático pendiente.",
        )

        return context
