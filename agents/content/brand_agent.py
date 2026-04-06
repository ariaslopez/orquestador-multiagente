"""BrandAgent — verifica coherencia de marca y voz, aplica correcciones finales."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class BrandAgent(BaseAgent):
    name = "BrandAgent"
    description = "Verifica coherencia de marca, voz y estilo. Aplica correcciones finales."

    async def run(self, context: AgentContext) -> AgentContext:
        edited = context.get_data('content_edited') or ''
        brief_data = context.get_data('content_brief') or {}
        personality_key = brief_data.get('personality_key', 'analyst')

        self.log(context, "Verificando coherencia de marca...")

        prompt = f"""Eres el guardian de marca de un medio crypto profesional.

CONTENIDO:
{edited}

PERSONALIDAD OBJETIVO: {personality_key}

Verifica y corrige:

## CONSISTENCIA DE VOZ
- El tono es consistente de principio a fin? (si/no + ejemplo si no)
- La personalidad '{personality_key}' se mantiene? (si/no)

## CREDIBILIDAD
- Hay afirmaciones sin sustento? (lista)
- Se usa lenguaje de certeza donde deberia haber cautela? ('va a subir' vs 'podria subir')

## LLAMADA A LA ACCION
- Es clara y especifica?
- Invita a engagement?

## CONTENIDO FINAL CORREGIDO
(entrega la version final lista para publicar, sin comentarios editoriales)"""

        result = await self.llm(context, prompt, temperature=0.2)

        # Extraer el contenido final si el LLM lo separa claramente
        final_marker = '## CONTENIDO FINAL CORREGIDO'
        if final_marker in result:
            final_content = result.split(final_marker, 1)[1].strip()
        else:
            final_content = edited  # fallback: mantener editado si no hay seccion clara

        context.set_data('brand_notes', result)
        context.set_data('content_final', final_content)
        self.log(context, "Verificacion de marca completada")
        return context
