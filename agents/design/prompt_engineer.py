"""PromptEngineerAgent — genera prompts optimizados para generación de imágenes y assets."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class PromptEngineerAgent(BaseAgent):
    name = "PromptEngineerAgent"
    description = "Genera prompts optimizados para Midjourney, DALL-E y Stable Diffusion."

    async def run(self, context: AgentContext) -> AgentContext:
        ui_specs = context.get_data('ui_specs') or ''
        brand_identity = context.get_data('brand_identity') or ''
        a11y_audit = context.get_data('a11y_audit') or ''
        self.log(context, "Generando prompts de imagen y reporte final de diseño...")

        prompt = f"""Eres un prompt engineer especializado en generación de assets visuales para productos.

SOLICITUD: {context.user_input}

BRAND: {brand_identity[:1000]}
UI: {ui_specs[:800]}

Genera los prompts y el reporte final:

## PROMPTS DE IMAGEN

### Logo / Marca
**Midjourney**: `...`
**DALL-E**: `...`
**Stable Diffusion**: `...`

### Hero Image / Banner
**Midjourney**: `...`

### Ilustraciones de UI
**Midjourney**: `...` (x3 variantes por uso: onboarding, vacío, error)

### Avatar / Mascota (si aplica)
**Midjourney**: `...`

## GUÍA DE ESTILO PARA PROMPTS
- Estilo visual base: (flat, isometric, 3D, ilustración, foto)
- Paleta de colores a especificar en prompts
- Palabras clave de estilo consistentes
- Palabras a evitar (negative prompts)

# REPORTE DE DISEÑO COMPLETO — ENTREGABLES

## RESUMEN
Qué se definió en este sprint de diseño y qué está listo para implementar.

## ENTREGABLES
| Artefacto | Estado | Formato | Próximo paso |
|-----------|--------|---------|-------------|

## DEUDA DE DISEÑO
Decisiones tomadas provisionalmente que deben revisarse."""

        result = await self.llm(context, prompt, temperature=0.35)
        context.final_output = result
        context.pipeline_name = "DESIGN"
        self.log(context, "Reporte de diseño completo — DESIGN pipeline completado")
        return context
