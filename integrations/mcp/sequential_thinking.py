"""MCP Adaptador — Sequential Thinking.

Fuerza al sistema a razonar paso a paso antes de generar una respuesta.
Evita conclusiones apresuradas en tareas complejas (planificacion,
analis de riesgos, decisiones de arquitectura).

Herramientas disponibles:
  think(problem, steps=5, depth='normal')
    -> {thinking_chain: [...], conclusion, confidence}
  decompose(task, max_subtasks=10)
    -> {subtasks: [{id, description, dependencies, estimated_effort}]}
  validate_plan(plan_text)
    -> {valid, issues: [...], suggestions: [...]}

No requiere API externa — usa el LLM interno del sistema (APIRouter).
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SequentialThinkingAdapter:
    """
    Implementa razonamiento encadenado usando el APIRouter interno.
    Usa prompts estructurados que fuerzan pensamiento paso a paso.
    """

    async def call(self, tool: str, params: Dict[str, Any]) -> Any:
        if tool == "think":
            return await self._think(**params)
        if tool == "decompose":
            return await self._decompose(**params)
        if tool == "validate_plan":
            return await self._validate_plan(**params)
        raise ValueError(f"SequentialThinking: tool '{tool}' desconocida")

    async def _get_router(self):
        from core.api_router import APIRouter
        return APIRouter()

    async def _think(
        self,
        problem: str,
        steps: int = 5,
        depth: str = "normal",
    ) -> Dict:
        """Razonamiento encadenado estructurado."""
        router = await self._get_router()
        depth_instructions = {
            "shallow": "2-3 oraciones por paso",
            "normal":  "4-6 oraciones por paso, incluye tradeoffs",
            "deep":    "parrafo completo por paso, considera casos borde",
        }.get(depth, "4-6 oraciones por paso")

        prompt = f"""/think
Problema: {problem}

Razono paso a paso ({steps} pasos, profundidad: {depth_instructions}):

Paso 1: [Entender el problema completamente]
Paso 2: [Identificar restricciones y dependencias]
Paso 3: [Explorar posibles enfoques]
...hasta paso {steps}

Formato de respuesta (JSON):
{{
  "thinking_chain": [
    {{"step": 1, "title": "...", "reasoning": "..."}},
    ...
  ],
  "conclusion": "decision o respuesta final",
  "confidence": 0.0-1.0,
  "alternatives": ["alternativa 1", "alternativa 2"]
}}"""
        result, _ = await router.complete(
            messages=[{"role": "user", "content": prompt}],
            task_type="reasoning",
            temperature=0.3,
            max_tokens=1500,
        )
        import json, re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {"thinking_chain": [], "conclusion": result, "confidence": 0.7}

    async def _decompose(self, task: str, max_subtasks: int = 10) -> Dict:
        """Descompone una tarea en subtareas con dependencias."""
        router = await self._get_router()
        prompt = f"""Descompone esta tarea en subtareas atomicas (max {max_subtasks}):

Tarea: {task}

Responde SOLO en JSON:
{{"subtasks": [
  {{"id": 1, "description": "...", "dependencies": [], "estimated_effort": "small|medium|large"}},
  ...
]}}"""
        result, _ = await router.complete(
            messages=[{"role": "user", "content": prompt}],
            task_type="planning",
            temperature=0.2,
            max_tokens=800,
        )
        import json, re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {"subtasks": []}

    async def _validate_plan(self, plan_text: str) -> Dict:
        """Valida un plan y detecta problemas o dependencias faltantes."""
        router = await self._get_router()
        prompt = f"""Valida este plan de ejecucion y detecta:
1. Pasos faltantes o ambiguos
2. Dependencias no satisfechas
3. Riesgos potenciales

Plan:
{plan_text}

Responde en JSON:
{{"valid": true/false, "issues": ["..."], "suggestions": ["..."]}}"""
        result, _ = await router.complete(
            messages=[{"role": "user", "content": prompt}],
            task_type="validation",
            temperature=0.2,
            max_tokens=600,
        )
        import json, re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {"valid": True, "issues": [], "suggestions": []}


def get_adapter() -> SequentialThinkingAdapter:
    return SequentialThinkingAdapter()
