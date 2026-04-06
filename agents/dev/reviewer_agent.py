"""ReviewerAgent — Revisa el codigo generado y detecta bugs."""
from __future__ import annotations
from core.base_agent import BaseAgent
from core.context import AgentContext


class ReviewerAgent(BaseAgent):
    name = "ReviewerAgent"
    description = "Detecta bugs, errores de logica y mejoras en el codigo generado."

    async def run(self, context: AgentContext) -> AgentContext:
        generated = getattr(context, 'generated_files', {})
        if not generated:
            return context

        issues_found = []
        corrected_files = {}

        for file_path, code in generated.items():
            if not file_path.endswith(('.py', '.js', '.ts', '.go', '.java')):
                corrected_files[file_path] = code
                continue

            self.log(context, f"Revisando {file_path}...")
            prompt = f"""Eres un senior developer haciendo code review.
Revisa este archivo y corrige cualquier bug, error de logica o problema de seguridad.

Archivo: {file_path}
Codigo:
```
{code}
```

Si el codigo esta correcto, responde: APPROVED
Si hay problemas, devuelve el codigo corregido completo (sin explicaciones, solo el codigo)."""
            result = await self.llm(context, prompt, temperature=0.1)
            if result.strip().upper().startswith('APPROVED'):
                corrected_files[file_path] = code
                self.log(context, f"  {file_path}: APPROVED")
            else:
                corrected_files[file_path] = self._clean_code(result)
                issues_found.append(file_path)
                self.log(context, f"  {file_path}: CORREGIDO")

        context.generated_files = corrected_files
        context.review_issues = issues_found
        self.log(context, f"Review completo. Corregidos: {len(issues_found)} archivos")
        return context

    def _clean_code(self, text: str) -> str:
        import re
        match = re.search(r'```(?:\w+)?\n([\s\S]+?)```', text)
        return match.group(1).strip() if match else text.strip()
