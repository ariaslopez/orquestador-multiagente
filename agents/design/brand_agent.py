"""DesignBrandAgent — guías de marca, naming y identidad visual."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class DesignBrandAgent(BaseAgent):
    name = "DesignBrandAgent"
    description = "Define identidad de marca: naming, voz, paleta, tipografía y guías de uso."

    async def run(self, context: AgentContext) -> AgentContext:
        ui_specs = context.get_data('ui_specs') or ''
        ux_architecture = context.get_data('ux_architecture') or ''
        self.log(context, "Definiendo identidad de marca...")

        prompt = f"""Eres un brand strategist y designer con experiencia en startups tecnológicas.

SOLICITUD: {context.user_input}

UI: {ui_specs[:800]}
UX: {ux_architecture[:800]}

Define la identidad de marca:

## NAMING
- Nombre propuesto: + justificación
- Alternativas (x3): + pros/contras
- Dominio: verificar disponibilidad de .com/.io
- Tagline: (máx 6 palabras)

## PERSONALIDAD DE MARCA
- Arquetipos (Jung): cuál encaja y por qué
- Adjetivos de marca (x5): confiable, audaz, etc.
- Voz y tono: formal/informal, técnico/accesible

## IDENTIDAD VISUAL
- Paleta primaria: 2 colores con hex + justificación psicológica
- Paleta secundaria: 3 colores de soporte
- Tipografía: fuente principal + secundaria (Google Fonts)
- Estilo de iconografía: outline/filled, nivel de detalle

## GUÍAS DE USO
- Qué NO hacer con el logo/marca
- Espaciado mínimo del logo
- Versiones permitidas (color, mono, negativo)"""

        result = await self.llm(context, prompt, temperature=0.35)
        context.set_data('brand_identity', result)
        self.log(context, "Identidad de marca definida")
        return context
