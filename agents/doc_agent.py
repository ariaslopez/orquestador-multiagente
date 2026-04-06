"""Agente que carga y procesa la documentación encontrada."""
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class DocAgent(BaseAgent):
    """Carga el contenido completo de los documentos más relevantes."""

    def __init__(self, max_docs: int = 3):
        super().__init__(
            name="DocAgent",
            description="Carga y procesa documentación local"
        )
        self.max_docs = max_docs

    def run(self, context: AgentContext) -> AgentContext:
        docs = []
        top_results = context.search_results[:self.max_docs]

        for result in top_results:
            try:
                path = Path(result["file"])
                content = path.read_text(encoding="utf-8")
                docs.append({
                    "source": result["file"],
                    "content": content,
                    "language": context.detected_language,
                })
            except Exception as e:
                context.add_error(self.name, f"Error cargando {result['file']}: {e}")

        context.relevant_docs = docs
        return context
