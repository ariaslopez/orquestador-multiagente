"""OutputManager — Gestiona la entrega de resultados según el tipo de tarea."""
from __future__ import annotations
import os
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OutputManager:
    """
    Gestiona dónde y cómo se guardan los resultados de cada pipeline.
    Cada tipo de tarea tiene un formato de output diferente.
    """

    OUTPUT_FORMATS = {
        "dev": "directory",       # Proyecto completo en carpeta
        "research": "markdown",   # Archivo .md con la tesis
        "content": "markdown",    # Archivo .md con el contenido
        "office": "report",       # Reporte + archivo procesado
        "qa": "markdown",         # Reporte de calidad
        "pm": "markdown",         # Backlog estructurado
        "trading": "report",      # Análisis de performance
    }

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or os.getenv("OUTPUT_PATH", "./output")
        Path(self.base_path).mkdir(parents=True, exist_ok=True)

    def get_output_path(self, task_type: str, name: str) -> str:
        """Genera la ruta de output para una tarea."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:50]

        if task_type == "dev":
            path = Path(self.base_path) / "projects" / f"{safe_name}"
        elif task_type == "research":
            path = Path(self.base_path) / "research" / f"tesis_{safe_name}_{timestamp}.md"
        elif task_type == "content":
            path = Path(self.base_path) / "content" / f"content_{safe_name}_{timestamp}.md"
        elif task_type in ("qa", "pm"):
            path = Path(self.base_path) / task_type / f"report_{safe_name}_{timestamp}.md"
        elif task_type in ("office", "trading"):
            path = Path(self.base_path) / task_type / f"analysis_{safe_name}_{timestamp}"
        else:
            path = Path(self.base_path) / "misc" / f"{safe_name}_{timestamp}"

        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    def save_markdown(self, content: str, path: str) -> str:
        """Guarda contenido Markdown en disco."""
        if not path.endswith(".md"):
            path += ".md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Output guardado: {path}")
        return path

    def save_json(self, data: dict, path: str) -> str:
        """Guarda datos JSON en disco."""
        if not path.endswith(".json"):
            path += ".json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Output JSON guardado: {path}")
        return path

    def ensure_project_dir(self, path: str) -> str:
        """Crea la estructura base de un proyecto generado."""
        project_path = Path(path)
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "logs").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        return str(project_path)

    def get_summary(self, task_type: str, output_path: str) -> str:
        """Genera un resumen del output para mostrar al usuario."""
        if task_type == "dev":
            path = Path(output_path)
            if path.exists():
                files = list(path.rglob("*"))
                py_files = [f for f in files if f.suffix == ".py"]
                return f"📁 Proyecto en: {output_path}\n   {len(py_files)} archivos Python generados"
        elif task_type in ("research", "content", "qa", "pm"):
            return f"📝 Reporte en: {output_path}"
        elif task_type in ("office", "trading"):
            return f"📊 Análisis en: {output_path}"
        return f"✅ Output en: {output_path}"
