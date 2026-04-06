"""BugHunterAgent — detecta bugs logicos, edge cases y null pointer dereferences."""
from __future__ import annotations
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class BugHunterAgent(BaseAgent):
    name = "BugHunterAgent"
    description = "Caza bugs logicos, edge cases y errores de manejo de estado."

    async def run(self, context: AgentContext) -> AgentContext:
        static_analysis = context.get_data('static_analysis') or ''
        code = self._load_code(context)
        self.log(context, "Cazando bugs...")

        prompt = f"""Eres un QA engineer senior especializado en encontrar bugs antes de produccion.

CODIGO A ANALIZAR:
{code[:3500]}

ANALISIS ESTATICO PREVIO:
{static_analysis[:500]}

ENFOCATE EN:
## BUGS CRITICOS (bloqueantes — causarian crash o comportamiento incorrecto grave)
Para cada bug:
- Ubicacion (funcion/linea estimada)
- Descripcion del problema
- Escenario de reproduccion
- Impacto

## BUGS MENORES (degradan UX pero no bloquean)
Mismo formato.

## EDGE CASES NO MANEJADOS
- Inputs vacios o None
- Valores limite (0, -1, listas vacias)
- Concurrencia / race conditions
- Timeouts no manejados

## NULL / UNDEFINED REFERENCES
- Variables usadas antes de inicializar
- Accesos a atributos sin verificar existencia

## TOTAL DE BUGS ENCONTRADOS: X criticos, Y menores"""

        result = await self.llm(context, prompt, temperature=0.1)
        context.set_data('bugs_found', result)
        self.log(context, "Bug hunting completado")
        return context

    def _load_code(self, context: AgentContext) -> str:
        input_file = getattr(context, 'input_file', None)
        input_repo = getattr(context, 'input_repo', None)
        if input_file and Path(input_file).exists():
            return Path(input_file).read_text(encoding='utf-8')
        if input_repo:
            return f"Repositorio: {input_repo}\n{context.user_input}"
        return context.user_input
