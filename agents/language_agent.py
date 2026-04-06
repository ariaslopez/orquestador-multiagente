"""Agente que detecta el lenguaje de programación en la consulta."""
import re
from core.base_agent import BaseAgent
from core.context import AgentContext

LANGUAGE_KEYWORDS = {
    "python": ["python", "pip", "django", "flask", "fastapi", "pandas", "numpy", ".py"],
    "javascript": ["javascript", "js", "node", "npm", "react", "vue", "typescript", ".js", ".ts"],
    "java": ["java", "maven", "gradle", "spring", "jvm", ".java"],
    "csharp": ["c#", "csharp", ".net", "dotnet", "asp.net", ".cs"],
    "go": ["golang", " go ", "goroutine", ".go"],
    "rust": ["rust", "cargo", "crate", ".rs"],
    "cpp": ["c++", "cpp", "cmake", ".cpp", ".h"],
    "php": ["php", "laravel", "composer", ".php"],
    "ruby": ["ruby", "rails", "gem", ".rb"],
    "kotlin": ["kotlin", ".kt"],
    "swift": ["swift", "xcode", ".swift"],
}


class LanguageAgent(BaseAgent):
    """Detecta el lenguaje de programación mencionado en la consulta."""

    def __init__(self):
        super().__init__(
            name="LanguageAgent",
            description="Detecta el lenguaje de programación relevante para la consulta"
        )

    def run(self, context: AgentContext) -> AgentContext:
        query_lower = context.user_query.lower()
        detected = None
        max_matches = 0

        for lang, keywords in LANGUAGE_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            if matches > max_matches:
                max_matches = matches
                detected = lang

        # Si hay archivos adjuntos, inferir del nombre/extensión
        if not detected and context.user_files:
            for f in context.user_files:
                name = str(f).lower()
                for lang, keywords in LANGUAGE_KEYWORDS.items():
                    if any(ext in name for ext in keywords if ext.startswith(".")):
                        detected = lang
                        break

        context.detected_language = detected or "general"
        context.set_meta("language_confidence", max_matches)
        return context
