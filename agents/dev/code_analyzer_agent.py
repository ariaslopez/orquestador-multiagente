"""CodeAnalyzerAgent — Analiza archivos de código adjuntos a la tarea.

Migrado de agents/code_agent.py (v1) a agents/dev/ en PR-2.
Renombrado a CodeAnalyzerAgent para diferenciarlo de:
  - agents/dev/coder_agent.py (GENERA código nuevo)

Este agente ANALIZA código existente (AST, líneas, funciones, clases,
errores de sintaxis). Se activa solo si ctx.input_file está presente.

Adaptaciones:
  - BaseAgent v2: run(ctx: AgentContext) async
  - ctx.input_file en lugar de context.user_files
  - ctx.set_data() en lugar de context.code_analysis
"""
from __future__ import annotations
import ast
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class CodeAnalyzerAgent(BaseAgent):
    """Analiza AST, estructura y errores de syntax de archivos .py adjuntos."""

    name        = "CodeAnalyzerAgent"
    description = "Analiza código fuente adjunto: funciones, clases, errores de sintaxis."

    async def run(self, ctx: AgentContext) -> AgentContext:
        if not ctx.input_file:
            self.log(ctx, "[CodeAnalyzerAgent] sin input_file — saltando")
            ctx.set_data("code_analysis", None)
            return ctx

        analysis: dict = {
            "file":          ctx.input_file,
            "total_lines":   0,
            "functions":     [],
            "classes":       [],
            "issues":        [],
            "language":      ctx.get_data("detected_language", "unknown"),
        }

        path = Path(ctx.input_file)
        if not path.exists():
            self.log(ctx, f"[CodeAnalyzerAgent] archivo no encontrado: {ctx.input_file}")
            ctx.set_data("code_analysis", analysis)
            return ctx

        try:
            content = path.read_text(encoding="utf-8")
            lines   = content.splitlines()
            analysis["total_lines"] = len(lines)

            # Análisis AST solo para Python
            if path.suffix == ".py":
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            analysis["functions"].append(node.name)
                        elif isinstance(node, ast.ClassDef):
                            analysis["classes"].append(node.name)
                except SyntaxError as e:
                    analysis["issues"].append(f"SyntaxError: {e}")
                    self.log(ctx, f"[CodeAnalyzerAgent] SyntaxError: {e}")

        except Exception as exc:
            analysis["issues"].append(str(exc))
            self.log(ctx, f"[CodeAnalyzerAgent] error leyendo archivo: {exc}")

        ctx.set_data("code_analysis", analysis)
        self.log(
            ctx,
            f"[CodeAnalyzerAgent] {analysis['total_lines']} líneas — "
            f"{len(analysis['functions'])} funciones — "
            f"{len(analysis['classes'])} clases",
        )
        return ctx
