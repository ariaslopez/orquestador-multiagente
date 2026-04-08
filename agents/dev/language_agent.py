"""LanguageAgent — Detecta el lenguaje de programación en la tarea.

Migrado de agents/language_agent.py (v1) a agents/dev/ en PR-2.
Adaptaciones:
  - BaseAgent v2: run(ctx: AgentContext) async
  - ctx.user_input en lugar de context.user_query
  - ctx.set_data() en lugar de context.detected_language
  - ctx.input_file para inferir lenguaje por extensión

Uso típico: primera etapa del pipeline DEV para que
PlannerAgent y CoderAgent ya sepan el lenguaje objetivo.
"""
from __future__ import annotations
import re
from core.base_agent import BaseAgent
from core.context import AgentContext

LANGUAGE_KEYWORDS: dict[str, list[str]] = {
    "python":     ["python", "pip", "django", "flask", "fastapi", "pandas", "numpy", ".py"],
    "javascript": ["javascript", "js", "node", "npm", "react", "vue", "typescript", ".js", ".ts"],
    "java":       ["java", "maven", "gradle", "spring", "jvm", ".java"],
    "csharp":     ["c#", "csharp", ".net", "dotnet", "asp.net", ".cs"],
    "go":         ["golang", " go ", "goroutine", ".go"],
    "rust":       ["rust", "cargo", "crate", ".rs"],
    "cpp":        ["c++", "cpp", "cmake", ".cpp", ".h"],
    "php":        ["php", "laravel", "composer", ".php"],
    "ruby":       ["ruby", "rails", "gem", ".rb"],
    "kotlin":     ["kotlin", ".kt"],
    "swift":      ["swift", "xcode", ".swift"],
}


class LanguageAgent(BaseAgent):
    """Detecta el lenguaje de programación de la tarea y lo guarda en ctx.data."""

    name        = "LanguageAgent"
    description = "Detecta el lenguaje de programación objetivo de la tarea DEV"

    async def run(self, ctx: AgentContext) -> AgentContext:
        text_lower = ctx.user_input.lower()
        detected: str | None = None
        max_matches = 0

        for lang, keywords in LANGUAGE_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > max_matches:
                max_matches = matches
                detected = lang

        # Inferir por extensión del archivo adjunto si no se detectó por texto
        if not detected and ctx.input_file:
            fname = ctx.input_file.lower()
            for lang, keywords in LANGUAGE_KEYWORDS.items():
                if any(ext in fname for ext in keywords if ext.startswith(".")):
                    detected = lang
                    break

        result = detected or "general"
        ctx.set_data("detected_language", result)
        ctx.set_data("language_confidence", max_matches)
        self.log(ctx, f"[LanguageAgent] lenguaje detectado: {result} (score={max_matches})")
        return ctx
