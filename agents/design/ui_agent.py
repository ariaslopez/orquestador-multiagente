"""UIAgent — genera especificaciones de componentes UI y sistemas de diseño."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class UIAgent(BaseAgent):
    name = "UIAgent"
    description = "Genera especificaciones detalladas de componentes UI y sistemas de diseño."

    async def run(self, context: AgentContext) -> AgentContext:
        self.log(context, "Generando especificaciones de UI...")

        prompt = f"""Eres un UI designer senior especializado en design systems y componentes.

SOLICITUD: {context.user_input}

Genera las especificaciones de UI completas:

## DESIGN SYSTEM BASE
- Grid: columnas, gutters, breakpoints
- Espaciado: escala base (4px/8px system)
- Tipografía: familias, escala de tamaños, pesos
- Colores: primarios, secundarios, semánticos (error, success, warning)
- Elevación/sombras: escala de shadows
- Border radius: escala

## COMPONENTES PRINCIPALES
Por cada componente:
```
Nombre: [Button / Card / Modal / etc.]
Variantes: [primary, secondary, ghost...]
Estados: [default, hover, active, disabled, loading]
Props: [label, onClick, variant, size, disabled]
Dimensiones: [padding, min-width, height]
```

## LAYOUT PATTERNS
Patrones de layout para las vistas principales del producto.

## DESIGN TOKENS
Tokens en formato CSS variables o JSON para implementación."""

        result = await self.llm(context, prompt, temperature=0.3)
        context.set_data('ui_specs', result)
        self.log(context, "Especificaciones de UI generadas")
        return context
