"""QAAgent — Audita codigo en busca de bugs, vulnerabilidades y gaps de tests."""
from __future__ import annotations
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class QAAgent(BaseAgent):
    name = "QAAgent"
    description = "Audita codigo existente: bugs, seguridad, performance y cobertura de tests."

    async def run(self, context: AgentContext) -> AgentContext:
        input_repo = getattr(context, 'input_repo', None)
        input_file = getattr(context, 'input_file', None)
        code_content = ''

        if input_file and Path(input_file).exists():
            code_content = Path(input_file).read_text(encoding='utf-8')
            self.log(context, f"Auditando archivo: {input_file}")
        elif input_repo:
            code_content = f"Repositorio a auditar: {input_repo}"
            self.log(context, f"Auditando repo: {input_repo}")
        else:
            code_content = context.user_input

        prompt = f"""Eres un senior QA engineer y security auditor.
Realiza una auditoria completa del siguiente codigo/descripcion:

{code_content[:4000]}

PETICION: {context.user_input}

Genera un reporte con:
## 1. BUGS CRITICOS (bloqueantes)
## 2. BUGS MENORES (no bloqueantes)
## 3. VULNERABILIDADES DE SEGURIDAD
## 4. PROBLEMAS DE PERFORMANCE
## 5. GAPS DE COBERTURA DE TESTS
## 6. CORRECCIONES SUGERIDAS (codigo concreto)
## 7. SCORE DE CALIDAD (0-100)

Se especifico y accionable."""
        report = await self.llm(context, prompt, temperature=0.1)
        context.final_output = report
        context.pipeline_name = "QA"
        self.log(context, "Auditoria QA completada")
        return context
