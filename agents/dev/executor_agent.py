"""ExecutorAgent — Escribe los archivos en disco e instala dependencias."""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext

ALLOWED_COMMANDS = ['pip install', 'npm install', 'yarn install', 'cargo build', 'go mod tidy']


class ExecutorAgent(BaseAgent):
    name = "ExecutorAgent"
    description = "Escribe los archivos en disco e instala las dependencias del proyecto."

    async def run(self, context: AgentContext) -> AgentContext:
        generated = getattr(context, 'generated_files', {})
        plan = getattr(context, 'plan', {})
        output_dir = Path(context.output_path or f"output/{plan.get('project_name', 'project')}")
        output_dir.mkdir(parents=True, exist_ok=True)

        written = []
        for file_path, content in generated.items():
            full_path = output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            written.append(str(file_path))
            self.log(context, f"  Escrito: {file_path}")

        # Instalar dependencias si requirements.txt fue generado
        req_file = output_dir / 'requirements.txt'
        if req_file.exists():
            self.log(context, "Instalando dependencias...")
            try:
                result = subprocess.run(
                    ['pip', 'install', '-r', str(req_file)],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode == 0:
                    self.log(context, "✅ Dependencias instaladas")
                else:
                    self.log(context, f"⚠ pip warning: {result.stderr[:200]}")
            except subprocess.TimeoutExpired:
                self.log(context, "⚠ Timeout instalando dependencias")
            except Exception as e:
                self.log(context, f"⚠ Error instalando: {e}")

        context.files_written = written
        context.final_output = (
            f"Proyecto generado en: {output_dir}\n"
            f"Archivos: {len(written)}\n"
            + "\n".join(f"  - {f}" for f in written)
        )
        self.log(context, f"✅ Proyecto listo en {output_dir}")
        return context
