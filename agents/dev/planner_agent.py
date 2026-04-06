"""PlannerAgent — Convierte descripcion en arbol de archivos + stack."""
from __future__ import annotations
import json
import re
from core.base_agent import BaseAgent
from core.context import AgentContext


class PlannerAgent(BaseAgent):
    name = "PlannerAgent"
    description = "Genera el plan de archivos, estructura y stack tecnologico del proyecto."

    async def run(self, context: AgentContext) -> AgentContext:
        self.log(context, "Generando plan de proyecto...")
        prompt = f"""Eres un arquitecto de software experto.
Analiza este requerimiento y genera un plan detallado en JSON:

REQUERIMIENTO:
{context.user_input}

Devuelve SOLO JSON con esta estructura:
{{
  "project_name": "nombre-del-proyecto",
  "description": "descripcion breve",
  "stack": ["tecnologia1", "tecnologia2"],
  "files": [
    {{"path": "main.py", "description": "punto de entrada", "priority": 1}},
    {{"path": "requirements.txt", "description": "dependencias", "priority": 1}}
  ],
  "install_commands": ["pip install -r requirements.txt"],
  "run_command": "python main.py",
  "estimated_files": 5
}}"""
        response = await self.llm(context, prompt, temperature=0.3)
        try:
            plan = json.loads(self._extract_json(response))
        except Exception:
            plan = {
                "project_name": "project",
                "files": [],
                "stack": [],
                "install_commands": [],
                "run_command": "python main.py",
            }

        # Sanitizar project_name: lowercase, espacios -> guiones, solo alfanumerico y guiones
        raw_name = plan.get('project_name', 'project') or 'project'
        safe_name = re.sub(r'[^a-z0-9\-]', '-', raw_name.lower().replace(' ', '-'))
        safe_name = re.sub(r'-+', '-', safe_name).strip('-') or 'project'
        plan['project_name'] = safe_name

        context.set_data('plan', plan)
        context.set_data('pipeline_name', 'DEV')
        self.log(context, f"Plan generado: {len(plan.get('files', []))} archivos | proyecto: {safe_name} | stack: {plan.get('stack', [])}")
        return context

    def _extract_json(self, text: str) -> str:
        import re
        match = re.search(r'```(?:json)?\s*([\s\S]+?)```', text)
        if match:
            return match.group(1).strip()
        start = text.find('{')
        end = text.rfind('}') + 1
        return text[start:end] if start != -1 else '{}'
