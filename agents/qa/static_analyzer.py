"""StaticAnalyzerAgent — linting, code smells, estructura y complejidad."""
from __future__ import annotations
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class StaticAnalyzerAgent(BaseAgent):
    name = "StaticAnalyzerAgent"
    description = "Analiza estaticamente el codigo: estructura, complejidad ciclomatica y code smells."

    async def run(self, context: AgentContext) -> AgentContext:
        code = self._load_code(context)
        self.log(context, f"Analisis estatico ({len(code)} chars)...")

        prompt = f"""Eres un senior software engineer especializado en calidad de codigo.
Realiza un analisis ESTATICO exhaustivo del siguiente codigo:

{code[:4000]}

PETICION: {context.user_input}

Analiza y reporta:
## ESTRUCTURA DEL CODIGO
- Organizacion de modulos/clases/funciones
- Separacion de responsabilidades (SRP)
- Niveles de abstraccion

## COMPLEJIDAD CICLOMATICA
- Funciones con complejidad > 10 (lista con valores estimados)
- Funciones demasiado largas (> 50 lineas)
- Profundidad de anidamiento excesiva (> 3 niveles)

## CODE SMELLS DETECTADOS
- Codigo duplicado
- Magic numbers/strings
- Nombres poco descriptivos
- Dead code
- God classes/functions

## VIOLACIONES DE PRINCIPIOS SOLID
- Lista concreta con ubicacion en el codigo

## SCORE DE ESTRUCTURA (0-100)
Justifica el score.

Se especifico: cita lineas o funciones concretas cuando sea posible."""

        result = await self.llm(context, prompt, temperature=0.1)
        context.set_data('static_analysis', result)
        self.log(context, "Analisis estatico completado")
        return context

    def _load_code(self, context: AgentContext) -> str:
        input_file = getattr(context, 'input_file', None)
        input_repo = getattr(context, 'input_repo', None)
        if input_file and Path(input_file).exists():
            return Path(input_file).read_text(encoding='utf-8')
        if input_repo:
            return f"Repositorio a auditar: {input_repo}\n\nDescripcion: {context.user_input}"
        return context.user_input
