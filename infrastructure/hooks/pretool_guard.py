#!/usr/bin/env python3
"""
Hook: PreToolUse
Se ejecuta ANTES de que el agente use una herramienta (Write, Bash, Edit).

Protege:
  - Workspace boundaries: bloquea escrituras fuera del directorio permitido
  - Paths protegidos del sistema operativo
  - Comandos Bash peligrosos (rm -rf /, sudo, etc.)

Exit codes:
  0 = permitir la acción
  2 = BLOQUEAR la acción (Claude recibe el mensaje de error)
"""

import json
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Paths del sistema que nunca deben ser modificados
SYSTEM_PROTECTED = [
    "/etc", "/usr", "/bin", "/sbin", "/boot", "/sys", "/proc",
    "/Windows", "/System32", "C:\\Windows", "C:\\System32",
    "/Users", "/Library", "/root",
]

# Patrones de comandos Bash peligrosos
DANGEROUS_BASH_PATTERNS = [
    "rm -rf /",  "rm -rf ~",  "mkfs",    "dd if=",
    ":(){ :|:& };",  "chmod 777 /",  "sudo rm",
    "format c:",  "> /dev/sda",
]


def is_protected_path(path: str, workspace: str) -> tuple[bool, str]:
    """Retorna (bloqueado, motivo)."""
    try:
        target = Path(path).resolve()
        ws     = Path(workspace).resolve()

        # Bloquear si el path apunta a carpetas del sistema
        for protected in SYSTEM_PROTECTED:
            if str(target).startswith(protected):
                return True, f"Path protegido del sistema: {protected}"

        # Bloquear si el path está FUERA del workspace
        try:
            target.relative_to(ws)
        except ValueError:
            return True, f"Path fuera del workspace permitido: {workspace}"

    except Exception as e:
        return False, ""  # en caso de error, permitir (no bloquear por defecto)

    return False, ""


def is_dangerous_bash(command: str) -> tuple[bool, str]:
    """Detecta comandos Bash peligrosos."""
    cmd_lower = command.lower()
    for pattern in DANGEROUS_BASH_PATTERNS:
        if pattern.lower() in cmd_lower:
            return True, f"Comando peligroso detectado: {pattern}"
    return False, ""


def main():
    workspace = os.getenv("CLAW_WORKSPACE", ".")

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # si no hay payload, permitir

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    # --- Validar herramientas de escritura de archivos ---
    if tool_name in ("Write", "Edit", "MultiEdit", "create_or_update_file"):
        file_path = tool_input.get("path", tool_input.get("file_path", ""))
        if file_path:
            blocked, reason = is_protected_path(file_path, workspace)
            if blocked:
                print(json.dumps({"error": f"[pretool-guard] BLOQUEADO: {reason}"}))
                sys.exit(2)

    # --- Validar comandos Bash ---
    if tool_name in ("Bash", "bash", "shell", "run_command"):
        command = tool_input.get("command", "")
        blocked, reason = is_dangerous_bash(command)
        if blocked:
            print(json.dumps({"error": f"[pretool-guard] Comando bloqueado: {reason}"}))
            sys.exit(2)

    sys.exit(0)  # permitir


if __name__ == "__main__":
    main()
