"""ContentAgent — Genera contenido crypto con personalidades configurables."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext

PERSONALITIES = {
    'analyst': 'Eres un analista cripto senior con 10 anos de experiencia. Tono: tecnico, objetivo, basado en datos.',
    'trader': 'Eres un trader profesional. Tono: directo, enfocado en niveles de precio y momentum.',
    'educator': 'Eres un educador de cripto. Tono: didactico, accesible, con analogias claras.',
    'bullish': 'Eres un crypto enthusiast optimista. Tono: energico, positivo, enfocado en adopcion.',
    'neutral': 'Eres un periodista financiero neutral. Tono: balanceado, factual, sin sesgo.',
}


class ContentAgent(BaseAgent):
    name = "ContentAgent"
    description = "Genera contenido cripto estructurado con personalidad configurable."

    async def run(self, context: AgentContext) -> AgentContext:
        personality_key = getattr(context, 'personality', 'analyst')
        content_type = getattr(context, 'content_type', 'thread')
        personality = PERSONALITIES.get(personality_key, PERSONALITIES['analyst'])

        research_context = ''
        if hasattr(context, 'analysis_result') and context.analysis_result:
            research_context = f"\n\nCONTEXTO DE INVESTIGACION:\n{context.analysis_result[:1500]}"

        self.log(context, f"Generando {content_type} con personalidad '{personality_key}'...")
        prompt = f"""{personality}

Genera el siguiente contenido:
TIPO: {content_type}
TEMA: {context.user_input}
{research_context}

Formatos validos:
- thread: hilo de Twitter/X (8-10 tweets numerados, cada uno maximo 280 chars)
- post: post de analisis largo (500-800 palabras)
- newsletter: boletin semanal (800-1200 palabras, con secciones)
- report: reporte ejecutivo (400-600 palabras)

Genera el contenido completo y listo para publicar."""
        content = await self.llm(context, prompt, temperature=0.6)
        context.final_output = content
        context.pipeline_name = "CONTENT"
        self.log(context, f"Contenido generado ({len(content)} chars)")
        return context
