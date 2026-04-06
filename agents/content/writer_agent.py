"""WriterAgent — genera el borrador completo basado en el brief."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class WriterAgent(BaseAgent):
    name = "WriterAgent"
    description = "Redacta el borrador completo del contenido siguiendo el brief definido."

    async def run(self, context: AgentContext) -> AgentContext:
        brief_data = context.get_data('content_brief') or {}
        brief = brief_data.get('brief', '')
        personality = brief_data.get('personality', 'Analitico, tecnico, basado en datos.')
        content_type = brief_data.get('content_type', 'thread')

        research_context = ''
        analysis = context.get_data('analysis_result') or getattr(context, 'analysis_result', None)
        if analysis:
            research_context = f"\n\nCONTEXTO DE INVESTIGACION:\n{str(analysis)[:1500]}"

        self.log(context, f"Redactando {content_type}...")

        format_instructions = {
            'thread': 'Hilo de Twitter/X: 8-10 tweets numerados. Cada tweet MAXIMO 280 caracteres. El primero es el hook. El ultimo es la CTA.',
            'post': 'Post de analisis: 500-800 palabras. Intro impactante, desarrollo con datos, conclusion accionable.',
            'newsletter': 'Boletin semanal: 800-1200 palabras. Secciones: Resumen ejecutivo, Analisis en profundidad, Datos clave, Oportunidades, Conclusion.',
            'report': 'Reporte ejecutivo: 400-600 palabras. TL;DR de 2 lineas, contexto, analisis, recomendacion.',
        }.get(content_type, 'Contenido estructurado y completo.')

        prompt = f"""{personality}

BRIEF DE CONTENIDO:
{brief[:1000]}
{research_context}

FORMATO REQUERIDO:
{format_instructions}

Genera el BORRADOR COMPLETO listo para edicion.
No incluyas meta-comentarios, solo el contenido."""

        draft = await self.llm(context, prompt, temperature=0.65)
        context.set_data('content_draft', draft)
        self.log(context, f"Borrador generado ({len(draft)} chars)")
        return context
