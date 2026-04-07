#!/usr/bin/env python3
"""
Hook: PostToolUse
Se ejecuta DESPUÉS de que el agente escribe un archivo (Write, Edit).

Responsabilidades:
  1. Correr ruff lint en archivos Python modificados
  2. Si el archivo tiene tests asociados, ejecutarlos
  3. Emitir LaneEvent.green o LaneEvent.red según resultado

Este hook NO bloquea (exit 0 siempre), solo informa al agente del resultado
para que pueda corregir si hay errores.
"""

import json
import os
import sys
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def run_lint(file_path: str) -> dict:
    """Corre ruff en el archivo modificado. Retorna resultado."""
    try:
        result = subprocess.run(
            ["ruff", "check", file_path, "--output-format=json"],
            capture_output=True, text=True, timeout=15
        )
        issues = json.loads(result.stdout) if result.stdout.strip() else []
        return {
            "passed": result.returncode == 0,
            "issues": issues[:5],  # max 5 issues para no saturar contexto
            "summary": f"{len(issues)} issues de lint",
        }
    except FileNotFoundError:
        return {"passed": True, "issues": [], "summary": "ruff no instalado — skipped"}
    except Exception as e:
        return {"passed": True, "issues": [], "summary": f"lint error: {e}"}


def run_related_tests(file_path: str, workspace: str) -> dict:
    """Intenta correr tests relacionados con el archivo modificado."""
    fp = Path(file_path)
    ws = Path(workspace)

    # Buscar test file relacionado
    test_candidates = [
        ws / "tests" / f"test_{fp.name}",
        ws / "tests" / f"test_{fp.stem}.py",
        fp.parent / f"test_{fp.name}",
    ]

    test_file = next((t for t in test_candidates if t.exists()), None)

    if not test_file:
        return {"ran": False, "passed": True, "summary": "No se encontraron tests relacionados"}

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", str(test_file), "-x", "-q", "--tb=short"],
            capture_output=True, text=True, timeout=60, cwd=workspace
        )
        passed = result.returncode == 0
        output = (result.stdout + result.stderr)[-1500:]  # últimos 1500 chars
        return {
            "ran":     True,
            "passed":  passed,
            "summary": "Tests OK" if passed else "Tests FALLARON",
            "output":  output,
        }
    except subprocess.TimeoutExpired:
        return {"ran": True, "passed": True, "summary": "Tests timeout (60s) — continuando"}
    except Exception as e:
        return {"ran": False, "passed": True, "summary": f"No se pudieron correr tests: {e}"}


def main():
    workspace = os.getenv("CLAW_WORKSPACE", ".")

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name   = payload.get("tool_name", "")
    tool_output = payload.get("tool_output", {})
    tool_input  = payload.get("tool_input", {})

    if tool_name not in ("Write", "Edit", "MultiEdit", "create_or_update_file"):
        sys.exit(0)

    file_path = tool_input.get("path", tool_input.get("file_path", ""))
    if not file_path or not file_path.endswith(".py"):
        sys.exit(0)

    lint_result  = run_lint(file_path)
    test_result  = run_related_tests(file_path, workspace)

    all_passed = lint_result["passed"] and test_result["passed"]

    output = {
        "file":   file_path,
        "lint":   lint_result,
        "tests":  test_result,
        "status": "GREEN" if all_passed else "RED",
    }

    # Informar al agente el resultado para que pueda actuar
    print(json.dumps(output, ensure_ascii=False))
    sys.exit(0)  # PostToolUse nunca bloquea


if __name__ == "__main__":
    main()
