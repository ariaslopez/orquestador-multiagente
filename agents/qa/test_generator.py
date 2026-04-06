"""TestGeneratorAgent — genera tests unitarios y de integracion basados en bugs encontrados."""
from __future__ import annotations
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class TestGeneratorAgent(BaseAgent):
    name = "TestGeneratorAgent"
    description = "Genera tests unitarios y de integracion para cubrir los bugs y gaps detectados."

    async def run(self, context: AgentContext) -> AgentContext:
        bugs_found = context.get_data('bugs_found') or ''
        security_issues = context.get_data('security_issues') or ''
        performance_issues = context.get_data('performance_issues') or ''
        static_analysis = context.get_data('static_analysis') or ''
        code = self._load_code(context)
        self.log(context, "Generando tests...")

        prompt = f"""Eres un QA automation engineer experto en pytest, unittest y testing moderno.

CODIGO BASE:
{code[:2000]}

BUGS ENCONTRADOS:
{bugs_found[:800]}

VULNERABILIDADES:
{security_issues[:500]}

PROBLEMAS DE PERFORMANCE:
{performance_issues[:300]}

Genera un suite de tests completo:

## TESTS UNITARIOS (pytest)
```python
# Genera tests reales ejecutables con pytest
# Usa mocks donde sea necesario
# Cubre cada bug critico encontrado
```

## TESTS DE INTEGRACION
```python
# Tests de flujos completos
# Verifica interaccion entre modulos
```

## TESTS DE SEGURIDAD
```python
# Tests que verifican que las vulnerabilidades estan parcheadas
# Input validation, auth checks, etc.
```

## REPORTE FINAL CONSOLIDADO

### RESUMEN EJECUTIVO
- Score de calidad: X/100
- Bugs criticos: N
- Vulnerabilidades: N
- Problemas de performance: N
- Tests generados: N

### TOP 5 ACCIONES INMEDIATAS (ordenadas por impacto)
1. ...
2. ...
3. ...
4. ...
5. ...

### ESTIMACION DE ESFUERZO DE REMEDIATION
(horas por categoria)"""

        result = await self.llm(context, prompt, temperature=0.2)
        context.final_output = result
        context.pipeline_name = "QA"
        self.log(context, "Suite de tests generado — QA pipeline completado")
        return context

    def _load_code(self, context: AgentContext) -> str:
        input_file = getattr(context, 'input_file', None)
        input_repo = getattr(context, 'input_repo', None)
        if input_file and Path(input_file).exists():
            return Path(input_file).read_text(encoding='utf-8')
        if input_repo:
            return f"Repositorio: {input_repo}\n{context.user_input}"
        return context.user_input
