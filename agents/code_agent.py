"""Agente que analiza código fuente si hay archivos adjuntos."""
import ast
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class CodeAgent(BaseAgent):
    """Analiza archivos de código adjuntos en la consulta."""

    def __init__(self):
        super().__init__(
            name="CodeAgent",
            description="Analiza código fuente de archivos adjuntos"
        )

    def can_run(self, context: AgentContext) -> bool:
        return bool(context.user_files)

    def run(self, context: AgentContext) -> AgentContext:
        analysis = {
            "files_analyzed": [],
            "total_lines": 0,
            "issues": [],
            "functions": [],
            "classes": [],
        }

        for file_path in context.user_files:
            path = Path(file_path)
            if not path.exists():
                continue

            try:
                content = path.read_text(encoding="utf-8")
                lines = content.splitlines()
                analysis["total_lines"] += len(lines)
                analysis["files_analyzed"].append(str(path))

                # Análisis básico Python
                if path.suffix == ".py":
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                analysis["functions"].append(node.name)
                            elif isinstance(node, ast.ClassDef):
                                analysis["classes"].append(node.name)
                    except SyntaxError as e:
                        analysis["issues"].append(f"SyntaxError en {path.name}: {e}")

            except Exception as e:
                context.add_error(self.name, str(e))

        context.code_analysis = analysis
        return context
