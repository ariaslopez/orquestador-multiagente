"""TopicAgent — analiza el input y define brief de contenido: tema, angulo, personalidad."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext

PERSONALITIES = {
    'analyst': 'Analitico, tecnico, basado en datos. Audiencia: traders e inversores.',
    'trader': 'Directo, enfocado en precio y momentum. Audiencia: traders activos.',
    'educator': 'Didactico, accesible, con analogias. Audiencia: principiantes en crypto.',
    'bullish': 'Energico, positivo, enfocado en adopcion. Audiencia: comunidad crypto.',
    'neutral': 'Balanceado, factual, periodistico. Audiencia: lectores generales.',
}

CONTENT_TYPES = ['thread', 'post', 'newsletter', 'report']


class TopicAgent(BaseAgent):
    name = "TopicAgent"
    description = "Define el brief de contenido: tema principal, angulo narrativo y personalidad."

    async def run(self, context: AgentContext) -> AgentContext:
        personality_key = getattr(context, 'personality', 'analyst')
        content_type = getattr(context, 'content_type', 'thread')

        # Validar que la personalidad y tipo sean validos
        if personality_key not in PERSONALITIES:
            personality_key = 'analyst'
        if content_type not in CONTENT_TYPES:
            content_type = 'thread'

        self.log(context, f"Definiendo brief ({content_type} / {personality_key})...")

        prompt = f"""Eres un estratega de contenido crypto senior.

TEMA SOLICITADO: {context.user_input}
TIPO DE CONTENIDO: {content_type}
PERSONALIDAD: {PERSONALITIES[personality_key]}

Define el brief de contenido:

## TEMA PRINCIPAL
(una frase concisa)

## ANGULO NARRATIVO
(por que es relevante AHORA, que hace unico este angulo)

## PUNTOS CLAVE A CUBRIR
(3-5 puntos ordenados por importancia)

## TONO Y ESTILO
(caracteristicas especificas para este contenido)

## LLAMADA A LA ACCION
(que quieres que haga el lector al terminar)

## PALABRAS CLAVE / HASHTAGS
(5-8 hashtags relevantes)

## FORMATO SUGERIDO
(estructura especifica para este tipo de contenido)"""

        brief = await self.llm(context, prompt, temperature=0.4)
        context.set_data('content_brief', {
            'brief': brief,
            'personality_key': personality_key,
            'content_type': content_type,
            'personality': PERSONALITIES[personality_key],
        })
        self.log(context, "Brief de contenido definido")
        return context
