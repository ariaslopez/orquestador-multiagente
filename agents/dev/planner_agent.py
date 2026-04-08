"""
PlannerAgent — Convierte descripción en árbol de archivos + stack + subtareas.

Estrategia:
  1. Si sequential_thinking MCP disponible → descompone en subtareas con dependencias
  2. LLM genera el plan JSON de archivos/stack (siempre, independiente del MCP)
  3. Combina ambos en ctx para que CoderAgent y ReviewerAgent consuman estructurado

Outputs en ctx:
  - ctx.data['plan']           : {project_name, files[], stack, run_command, ...}
  - ctx.data['subtasks']       : [{id, title, description, depends_on[], agent}, ...]
  - ctx.data['thinking_steps'] : pasos del sequential_thinking (debug)
  - ctx.data['pipeline_name']  : 'DEV'
"""
from __future__ import annotations
import json
import re
import logging
from core.base_agent import BaseAgent
from core.context import AgentContext

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    name = "PlannerAgent"
    description = "Genera plan de proyecto con árbol de archivos, stack y subtareas con dependencias."

    async def run(self, ctx: AgentContext) -> AgentContext:
        self.log(ctx, "[Planner] Iniciando planificación...")

        # --- Paso 1: sequential_thinking para descomposición de subtareas ---
        subtasks = []
        thinking_steps = []

        if ctx.is_mcp_available("sequential_thinking"):
            try:
                thinking_result = await ctx.mcp_call(
                    "sequential_thinking",
                    "sequentialthinking",
                    {
                        "thought": f"Descomponer en subtareas de desarrollo: {ctx.user_input}",
                        "nextThoughtNeeded": True,
                        "thoughtNumber": 1,
                        "totalThoughts": 5,
                    },
                )
                thinking_steps = thinking_result.get("thoughts", [])

                # Construir subtareas desde los pasos de pensamiento
                agents_map = {
                    "plan": "PlannerAgent",
                    "cod": "CoderAgent",
                    "test": "ReviewerAgent",
                    "review": "ReviewerAgent",
                    "exec": "ExecutorAgent",
                    "git": "GitAgent",
                    "doc": "CoderAgent",
                }
                for i, step in enumerate(thinking_steps):
                    content = step.get("thought", step) if isinstance(step, dict) else str(step)
                    agent_key = next(
                        (k for k in agents_map if k in content.lower()), "CoderAgent"
                    )
                    subtasks.append({
                        "id": i + 1,
                        "title": content[:80],
                        "description": content,
                        "depends_on": [i] if i > 0 else [],
                        "agent": agents_map.get(agent_key, "CoderAgent"),
                        "status": "pending",
                    })
                self.log(ctx, f"[Planner] sequential_thinking: {len(subtasks)} subtareas generadas")
            except Exception as exc:
                logger.warning("[Planner] sequential_thinking falló: %s — continuando sin subtareas MCP", exc)

        # --- Paso 2: LLM genera el plan JSON (siempre) ---
        prompt = f"""Eres un arquitecto de software experto.
Analiza este requerimiento y genera un plan detallado en JSON:

REQUERIMIENTO:
{ctx.user_input}

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

        response = await self.llm(ctx, prompt, temperature=0.3)

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

        # Sanitizar project_name
        raw_name = plan.get("project_name", "project") or "project"
        safe_name = re.sub(r"[^a-z0-9\-]", "-", raw_name.lower().replace(" ", "-"))
        safe_name = re.sub(r"-+", "-", safe_name).strip("-") or "project"
        plan["project_name"] = safe_name

        # Si no se generaron subtareas vía MCP, crear estructura mínima desde el plan
        if not subtasks and plan.get("files"):
            subtasks = [
                {
                    "id": i + 1,
                    "title": f"Implementar {f['path']}",
                    "description": f.get("description", f"Crear {f['path']}"),
                    "depends_on": [i] if i > 0 else [],
                    "agent": "CoderAgent",
                    "status": "pending",
                }
                for i, f in enumerate(plan["files"][:10])
            ]

        # --- Paso 3: Guardar en ctx ---
        ctx.set_data("plan", plan)
        ctx.set_data("subtasks", subtasks)
        ctx.set_data("thinking_steps", thinking_steps)
        ctx.set_data("pipeline_name", "DEV")

        self.log(
            ctx,
            f"[Planner] ✓ proyecto={safe_name} | "
            f"{len(plan.get('files', []))} archivos | "
            f"{len(subtasks)} subtareas | "
            f"stack={plan.get('stack', [])}",
        )
        return ctx

    def _extract_json(self, text: str) -> str:
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
        if match:
            return match.group(1).strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        return text[start:end] if start != -1 else "{}"
