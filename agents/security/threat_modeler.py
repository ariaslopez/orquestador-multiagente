"""ThreatModelerAgent — modelado de amenazas con STRIDE para sistemas y aplicaciones."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class ThreatModelerAgent(BaseAgent):
    name = "ThreatModelerAgent"
    description = "Modela amenazas usando STRIDE: identifica actores, vectores y superficie de ataque."

    async def run(self, context: AgentContext) -> AgentContext:
        file_content = context.get_data('file_content') or ''
        code_context = f"\n\nCÓDIGO/SISTEMA:\n{file_content[:2500]}" if file_content else ''
        self.log(context, "Modelando amenazas con STRIDE...")

        prompt = f"""Eres un security architect experto en threat modeling.

SISTEMA A AUDITAR: {context.user_input}{code_context}

Realiza el modelado de amenazas completo:

## SUPERFICIE DE ATAQUE
- Entry points: APIs, UI, archivos, variables de entorno
- Assets críticos: datos sensibles, credenciales, lógica de negocio
- Trust boundaries: qué confía en qué

## ANÁLISIS STRIDE
| Categoría | Amenaza identificada | Componente afectado | Severidad |
|-----------|--------------------|--------------------|----------|
| Spoofing | | | |
| Tampering | | | |
| Repudiation | | | |
| Information Disclosure | | | |
| Denial of Service | | | |
| Elevation of Privilege | | | |

## THREAT ACTORS
| Actor | Motivación | Capacidad | Vector principal |
|-------|-----------|-----------|------------------|

## TOP 5 AMENAZAS CRÍTICAS
Ordenadas por probabilidad × impacto.

## DIAGRAMA DE FLUJO DE DATOS (textual)
Descripción del flujo de datos y dónde ocurren las amenazas."""

        result = await self.llm(context, prompt, temperature=0.15)
        context.set_data('threat_model', result)
        self.log(context, "Modelado de amenazas completado")
        return context
