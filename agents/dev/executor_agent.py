"""ExecutorAgent — Escribe los archivos en disco e instala dependencias."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from core.base_agent import BaseAgent
from core.context import AgentContext


class ExecutorAgent(BaseAgent):
    name = "ExecutorAgent"
    description = "Escribe los archivos en disco e instala las dependencias del proyecto."

    async def run(self, context: AgentContext) -> AgentContext:
        generated = context.get_data('generated_files') or {}
        # project_dir ya fue calculado por CoderAgent con la subcarpeta correcta
        project_dir = Path(
            context.get_data('project_dir')
            or context.output_path
            or './output/project'
        )
        project_dir.mkdir(parents=True, exist_ok=True)

        written = []
        for file_path, content in generated.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            written.append(str(file_path))
            self.log(context, f"  Escrito: {file_path}")

        # Instalar dependencias si requirements.txt fue generado
        req_file = project_dir / 'requirements.txt'
        if req_file.exists():
            self.log(context, "Instalando dependencias...")
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '-r', str(req_file)],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    shell=False,
                )
                if result.returncode == 0:
                    self.log(context, "✅ Dependencias instaladas")
                else:
                    self.log(context, f"⚠ pip warning: {result.stderr[:200]}")
            except subprocess.TimeoutExpired:
                self.log(context, "⚠ Timeout instalando dependencias")
            except Exception as e:
                self.log(context, f"⚠ Error instalando: {e}")

        context.set_data('files_written', written)
        context.output_path = str(project_dir)
        context.final_output = (
            f"Proyecto generado en: {project_dir}\n"
            f"Archivos: {len(written)}\n"
            + "\n".join(f"  - {f}" for f in written)
            + f"\n\nPara ejecutar:\n  cd {project_dir}\n  {context.get_data('plan', {}).get('run_command', 'python main.py')}"
        )
        self.log(context, f"✅ Proyecto listo en {project_dir}")
        return context
