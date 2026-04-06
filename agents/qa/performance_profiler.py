"""PerformanceProfilerAgent — N+1, loops costosos, memory leaks, bottlenecks."""
from __future__ import annotations
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class PerformanceProfilerAgent(BaseAgent):
    name = "PerformanceProfilerAgent"
    description = "Detecta problemas de performance: N+1, algoritmos costosos, memory leaks."

    async def run(self, context: AgentContext) -> AgentContext:
        code = self._load_code(context)
        self.log(context, "Profiling de performance...")

        prompt = f"""Eres un performance engineer con experiencia en optimizacion de sistemas en produccion.

CODIGO:
{code[:3500]}

Analiza el performance del codigo:

## COMPLEJIDAD ALGORITMICA
- Funciones con complejidad O(n²) o peor
- Loops anidados innecesarios
- Sorting/searching ineficiente

## PROBLEMAS DE BASE DE DATOS
- Queries N+1 (listas de objetos con queries dentro de loops)
- Falta de indices obvios
- Queries sin limite/paginacion
- Transacciones demasiado largas

## MEMORIA
- Objetos grandes creados en loops
- Listas que crecen indefinidamente
- Caches sin limite ni TTL
- Leaks probables (recursos no cerrados)

## I/O Y RED
- Llamadas sincronas bloqueantes
- Falta de connection pooling
- Requests sin timeout
- Datos descargados completos cuando solo se necesita parte

## OPTIMIZACIONES SUGERIDAS
Para cada problema: solucion concreta con pseudocodigo o ejemplo.

## IMPACTO ESTIMADO EN PRODUCCION (ALTO/MEDIO/BAJO)"""

        result = await self.llm(context, prompt, temperature=0.1)
        context.set_data('performance_issues', result)
        self.log(context, "Profiling de performance completado")
        return context

    def _load_code(self, context: AgentContext) -> str:
        input_file = getattr(context, 'input_file', None)
        input_repo = getattr(context, 'input_repo', None)
        if input_file and Path(input_file).exists():
            return Path(input_file).read_text(encoding='utf-8')
        if input_repo:
            return f"Repositorio: {input_repo}\n{context.user_input}"
        return context.user_input
