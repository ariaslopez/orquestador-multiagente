"""CopyAgent — copywriting para landing, ads, emails y redes sociales."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class CopyAgent(BaseAgent):
    name = "CopyAgent"
    description = "Genera copywriting persuasivo para landing pages, ads y emails."

    async def run(self, context: AgentContext) -> AgentContext:
        strategy = context.get_data('marketing_strategy') or ''
        self.log(context, "Generando copy de marketing...")

        prompt = f"""Eres un copywriter senior especializado en SaaS y conversión.

SOLICITUD: {context.user_input}

ESTRATEGIA BASE:
{strategy[:2000]}

Genera el copy completo:

## LANDING PAGE
**Headline principal**: (máx 8 palabras, beneficio claro)
**Subheadline**: (amplía con propuesta de valor, máx 20 palabras)
**CTA principal**: (verbo de acción + beneficio)
**3 bullets de beneficios**: (feature → beneficio → resultado)

## EMAIL DE BIENVENIDA
Asunto: ...
Cuerpo: (150-200 palabras, tono conversacional)

## AD COPY (x3 variantes)
- Variante A (pain-focused): ...
- Variante B (benefit-focused): ...
- Variante C (social proof-focused): ...

## TAGLINES (x5)
Opciones de tagline para la marca."""

        result = await self.llm(context, prompt, temperature=0.4)
        context.set_data('marketing_copy', result)
        self.log(context, "Copy de marketing generado")
        return context
