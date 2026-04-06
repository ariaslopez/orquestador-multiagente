"""FileOpsTool — Operaciones de archivos con validación de seguridad."""
from __future__ import annotations
import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class FileOpsTool:
    """
    Crea, lee, escribe y organiza archivos del proyecto generado.
    Toda operación se realiza dentro de la carpeta de output permitida.
    """

    def __init__(self, sandbox_path: Optional[str] = None):
        self.sandbox_path = sandbox_path or os.getenv("OUTPUT_PATH", "./output")

    def _safe_path(self, path: str) -> Path:
        """Garantiza que la ruta esté dentro del sandbox."""
        full = Path(self.sandbox_path) / path
        full = full.resolve()
        sandbox = Path(self.sandbox_path).resolve()
        if not str(full).startswith(str(sandbox)):
            raise PermissionError(f"Ruta fuera del sandbox: {path}")
        return full

    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> str:
        """Escribe un archivo. Crea los directorios intermedios si no existen."""
        full_path = self._safe_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding=encoding) as f:
            f.write(content)
        logger.info(f"FileOps.write: {full_path}")
        return str(full_path)

    def read_file(self, path: str, encoding: str = "utf-8") -> str:
        """Lee un archivo y retorna su contenido."""
        full_path = Path(path).resolve()
        if not full_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        with open(full_path, "r", encoding=encoding, errors="ignore") as f:
            return f.read()

    def list_files(self, directory: str, pattern: str = "*") -> List[str]:
        """Lista archivos en un directorio."""
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        return [str(f) for f in dir_path.rglob(pattern) if f.is_file()]

    def ensure_dir(self, path: str) -> str:
        """Crea un directorio si no existe."""
        full_path = Path(path)
        full_path.mkdir(parents=True, exist_ok=True)
        return str(full_path)

    def copy_file(self, src: str, dst: str) -> str:
        """Copia un archivo."""
        shutil.copy2(src, dst)
        logger.info(f"FileOps.copy: {src} → {dst}")
        return dst

    def delete_file(self, path: str) -> None:
        """Elimina un archivo (solo dentro del sandbox)."""
        full_path = self._safe_path(path)
        if full_path.exists():
            full_path.unlink()
            logger.info(f"FileOps.delete: {full_path}")

    def get_file_stats(self, path: str) -> dict:
        """Retorna metadata de un archivo."""
        p = Path(path)
        if not p.exists():
            return {}
        stat = p.stat()
        return {
            "name": p.name,
            "size_bytes": stat.st_size,
            "extension": p.suffix,
            "exists": True,
        }
