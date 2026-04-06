"""CodeExecutorTool — Ejecuta comandos de forma segura con timeout."""
from __future__ import annotations
import os
import subprocess
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeExecutorTool:
    """
    Ejecuta comandos del sistema con:
    - Timeout configurable
    - Captura de stdout y stderr
    - Validación de seguridad previa
    """

    def __init__(self, sandbox=None, timeout: int = 60):
        self.sandbox = sandbox
        self.timeout = timeout

    def run(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Ejecuta un comando y retorna {stdout, stderr, returncode, success}.
        Si sandbox está disponible, valida el comando antes de ejecutar.
        """
        # Validar con sandbox si está disponible
        if self.sandbox and not self.sandbox.validate_command(command):
            return {
                "stdout": "",
                "stderr": f"Comando bloqueado por seguridad: {command}",
                "returncode": -1,
                "success": False,
                "blocked": True,
            }

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                cwd=cwd or os.getcwd(),
            )
            logger.info(f"Exec: '{command[:60]}' → rc={result.returncode}")
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "blocked": False,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Timeout después de {timeout or self.timeout}s",
                "returncode": -1,
                "success": False,
                "blocked": False,
            }
        except Exception as e:
            logger.error(f"CodeExecutor error: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "success": False,
                "blocked": False,
            }

    def install_package(self, package: str, manager: str = "pip") -> Dict:
        """Instala un paquete con pip o npm."""
        if manager == "pip":
            return self.run(f"pip install {package} --quiet")
        elif manager == "npm":
            return self.run(f"npm install {package}")
        return {"success": False, "stderr": f"Manager desconocido: {manager}"}
