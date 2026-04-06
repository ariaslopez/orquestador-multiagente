"""CoderAgent — Genera el codigo de cada archivo del plan."""
from __future__ import annotations
import os
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class CoderAgent(BaseAgent):
    name = "CoderAgent"
    description = "Genera el contenido real de cada archivo del proyecto."

    async def run(self, context: AgentContext) -> AgentContext:
        plan = getattr(context, 'plan', {})
        files = plan.get('files', [])
        if not files:
            self.log(context, "No hay archivos en el plan.")
            return context

        output_dir = Path(context.output_path or f"output/{plan.get('project_name', 'project')}")
        context.generated_files = {}

        for file_info in sorted(files, key=lambda x: x.get('priority', 99)):
            file_path = file_info['path']
            self.log(context, f"Generando {file_path}...")
            prompt = f"""Genera el contenido completo y funcional del archivo `{file_path}`.

Proyecto: {plan.get('description', context.user_input)}
Stack: {', '.join(plan.get('stack', []))}
Descripcion del archivo: {file_info.get('description', '')}

Reglas:
- Codigo completo y funcional, listo para produccion
- Manejo explicito de errores
- Variables descriptivas
- Sin placeholders ni TODOs sin implementar
- Solo el codigo, sin explicaciones adicionales"""
            code = await self.llm(context, prompt, temperature=0.2)
            code = self._clean_code(code)
            context.generated_files[file_path] = code
            self.log(context, f"  {file_path} generado ({len(code)} chars)")

        context.output_path = str(output_dir)
        self.log(context, f"Total: {len(context.generated_files)} archivos generados")
        return context

    def _clean_code(self, text: str) -> str:
        import re
        match = re.search(r'```(?:\w+)?\n([\s\S]+?)```', text)
        if match:
            return match.group(1).strip()
        return text.strip()
