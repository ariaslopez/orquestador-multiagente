"""EditorAgent — edita el borrador: tono, longitud, claridad, hashtags."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class EditorAgent(BaseAgent):
    name = "EditorAgent"
    description = "Edita el borrador: mejora tono, claridad, longitud y optimiza hashtags."

    async def run(self, context: AgentContext) -> AgentContext:
        draft = context.get_data('content_draft') or ''
        brief_data = context.get_data('content_brief') or {}
        content_type = brief_data.get('content_type', 'thread')
        personality = brief_data.get('personality', '')

        self.log(context, "Editando contenido...")

        prompt = f"""Eres un editor senior de contenido crypto. Tu trabajo es mejorar el borrador, no reescribirlo.

BORRADOR:
{draft}

TIPO: {content_type}
TONO OBJETIVO: {personality}

Edita aplicando:

1. CLARIDAD — elimina jerga innecesaria, simplifica sin perder profundidad
2. RITMO — varia longitud de frases, evita repeticiones
3. PRECISION — verifica que los numeros/afirmaciones sean especificos
4. LONGITUD — ajusta al formato objetivo sin padding innecesario
5. HASHTAGS — revisa relevancia y cantidad (max 5 para posts, incluir en threads al final)
6. HOOK — asegurate de que la primera linea/tweet sea imposible de ignorar

Entrega SOLO el contenido editado, sin comentarios editoriales.
Marca cambios significativos con [EDIT: razon] al final del bloque modificado."""

        edited = await self.llm(context, prompt, temperature=0.3)
        context.set_data('content_edited', edited)
        self.log(context, "Edicion completada")
        return context
