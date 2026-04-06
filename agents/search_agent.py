"""Agente que busca documentación relevante en la base de conocimiento local."""
import os
import json
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge_base" / "docs"


class SearchAgent(BaseAgent):
    """Busca archivos de documentación relevantes en el directorio local."""

    def __init__(self):
        super().__init__(
            name="SearchAgent",
            description="Busca documentación local relevante para la consulta"
        )

    def run(self, context: AgentContext) -> AgentContext:
        lang = context.detected_language or "general"
        query_words = set(context.user_query.lower().split())

        results = []
        search_path = KNOWLEDGE_BASE_PATH / lang

        # Si no hay carpeta para el lenguaje, busca en general
        if not search_path.exists():
            search_path = KNOWLEDGE_BASE_PATH

        if search_path.exists():
            for file_path in search_path.rglob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    content_words = set(content.lower().split())
                    # Score simple: palabras en común
                    score = len(query_words & content_words)
                    if score > 0:
                        results.append({
                            "file": str(file_path),
                            "score": score,
                            "preview": content[:300]
                        })
                except Exception:
                    continue

        # Ordena por relevancia
        results.sort(key=lambda x: x["score"], reverse=True)
        context.search_results = results[:5]  # Top 5
        return context
