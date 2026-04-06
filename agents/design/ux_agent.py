"""UXAgent — arquitectura de información, flujos de usuario y design tokens CSS."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class UXAgent(BaseAgent):
    name = "UXAgent"
    description = "Define arquitectura de información, user flows y estructura CSS del proyecto."

    async def run(self, context: AgentContext) -> AgentContext:
        ui_specs = context.get_data('ui_specs') or ''
        self.log(context, "Diseñando arquitectura UX y flujos de usuario...")

        prompt = f"""Eres un UX architect con experiencia en SaaS y productos complejos.

SOLICITUD: {context.user_input}

ESPECIFICACIONES UI:
{ui_specs[:1500]}

Define la arquitectura UX:

## ARQUITECTURA DE INFORMACIÓN
- Mapa del sitio / app con jerarquía de secciones
- Navegación principal y secundaria
- Breadcrumbs y orientación contextual

## USER FLOWS CRÍTICOS
Por cada flujo clave (onboarding, core action, upgrade):
1. Pantalla inicial → paso 1 → paso 2 → ... → éxito

## ESTRUCTURA CSS RECOMENDADA
```
styles/
├── tokens.css        (variables globales)
├── base.css          (reset + tipografía)
├── layout.css        (grid, containers)
├── components/       (un archivo por componente)
└── pages/            (overrides por vista)
```

## HEURÍSTICAS DE USABILIDAD
Top 5 principios Nielsen aplicados al diseño propuesto.

## MÉTRICAS UX A MONITOREAR
Tiempo en tarea, tasa de error, satisfacción (SUS score)."""

        result = await self.llm(context, prompt, temperature=0.25)
        context.set_data('ux_architecture', result)
        self.log(context, "Arquitectura UX definida")
        return context
