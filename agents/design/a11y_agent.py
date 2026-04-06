"""A11yAgent — auditoría de accesibilidad WCAG 2.1 nivel AA."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class A11yAgent(BaseAgent):
    name = "A11yAgent"
    description = "Audita accesibilidad según WCAG 2.1 AA: contraste, semántica, teclado y screen readers."

    async def run(self, context: AgentContext) -> AgentContext:
        ui_specs = context.get_data('ui_specs') or ''
        brand_identity = context.get_data('brand_identity') or ''
        self.log(context, "Auditando accesibilidad WCAG 2.1...")

        prompt = f"""Eres un experto en accesibilidad web certificado en WCAG 2.1.

SOLICITUD: {context.user_input}

UI SPECS: {ui_specs[:1000]}
BRAND: {brand_identity[:800]}

Realiza la auditoría de accesibilidad:

## CRITERIOS WCAG 2.1 — NIVEL AA
| Criterio | Código | Estado | Observación |
|---------|--------|--------|------------|
| Contraste texto normal | 1.4.3 | | ratio mínimo 4.5:1 |
| Contraste texto grande | 1.4.3 | | ratio mínimo 3:1 |
| Contraste UI components | 1.4.11 | | ratio mínimo 3:1 |
| Navegación por teclado | 2.1.1 | | |
| Focus visible | 2.4.7 | | |
| Skip links | 2.4.1 | | |
| Alt text en imágenes | 1.1.1 | | |
| Semántica HTML | 1.3.1 | | |
| ARIA labels | 4.1.2 | | |

## CONTRASTE DE COLORES
Calcula ratios de contraste para la paleta definida.

## PROBLEMAS CRÍTICOS (nivel A)
Fallas que bloquean el uso para personas con discapacidad.

## MEJORAS RECOMENDADAS (nivel AA)
Ajustes para alcanzar conformidad AA completa.

## CHECKLIST DE IMPLEMENTACIÓN
Lista de verificación para el equipo de desarrollo."""

        result = await self.llm(context, prompt, temperature=0.1)
        context.set_data('a11y_audit', result)
        self.log(context, "Auditoría de accesibilidad completada")
        return context
