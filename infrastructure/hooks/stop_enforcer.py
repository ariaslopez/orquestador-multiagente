#!/usr/bin/env python3
"""
Hook: Stop
Se ejecuta cuando el agente quiere TERMINAR su respuesta.

Si los tests globales del proyecto fallan, fuerza al agente a continuar
corrigiendo en lugar de detenerse con trabajo incompleto.

Este es el reemplazo del loop manual MAX_ITERATIONS:
  - En lugar de un loop externo que reintenta, el agente mismo sigue trabajando
  - Solo detiene cuando los tests pasan O se alcanza MAX_STOP_CALLS

Salidas:
  exit 0 + sin output   = stop normal (tests pasan)
  exit 0 + JSON {"decision": "continue", "reason": "..."} = forzar al agente a seguir
"""

import json
import os
import sys
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_STOP_CALLS  = int(os.getenv("CLAW_MAX_ITERATIONS", "5"))
STOP_CALL_FILE  = Path(".claw/.stop_count")  # contador de llamadas al hook


def get_stop_count() -> int:
    try:
        if STOP_CALL_FILE.exists():
            return int(STOP_CALL_FILE.read_text().strip())
    except:
        pass
    return 0


def increment_stop_count() -> int:
    count = get_stop_count() + 1
    STOP_CALL_FILE.parent.mkdir(parents=True, exist_ok=True)
    STOP_CALL_FILE.write_text(str(count))
    return count


def reset_stop_count():
    if STOP_CALL_FILE.exists():
        STOP_CALL_FILE.unlink()


def run_all_tests(workspace: str) -> dict:
    """Corre la suite completa de tests del proyecto."""
    tests_dir = Path(workspace) / "tests"
    if not tests_dir.exists():
        return {"ran": False, "passed": True, "summary": "No hay directorio tests/"}

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", str(tests_dir), "-x", "-q",
             "--tb=short", "--no-header"],
            capture_output=True, text=True, timeout=120, cwd=workspace
        )
        passed  = result.returncode == 0
        # Solo los últimos 2000 chars del output para no saturar el contexto
        output  = (result.stdout + result.stderr)[-2000:]
        return {
            "ran":     True,
            "passed":  passed,
            "summary": "Todos los tests pasan ✅" if passed else "Tests fallando ❌",
            "output":  output,
        }
    except subprocess.TimeoutExpired:
        return {"ran": True, "passed": True, "summary": "Tests timeout (120s) — permitiendo stop"}
    except Exception as e:
        return {"ran": False, "passed": True, "summary": f"No se pudieron correr tests: {e}"}


def main():
    workspace  = os.getenv("CLAW_WORKSPACE", ".")
    force_stop = os.getenv("CLAW_FORCE_STOP", "false").lower() == "true"

    # Si el modo es PLAN_ONLY o el entorno indica stop forzado, siempre detenerse
    if force_stop:
        reset_stop_count()
        sys.exit(0)

    stop_count = increment_stop_count()

    # Proteger contra loops infinitos
    if stop_count >= MAX_STOP_CALLS:
        logger.warning(f"Máximo de iteraciones alcanzado ({MAX_STOP_CALLS}). Forzando stop.")
        reset_stop_count()
        sys.exit(0)

    test_result = run_all_tests(workspace)

    if test_result["passed"]:
        # Tests pasan -> stop normal
        reset_stop_count()
        sys.exit(0)
    else:
        # Tests fallan -> forzar al agente a continuar y corregir
        reason = (
            f"Los tests del proyecto todavía fallan ❌ (iteración {stop_count}/{MAX_STOP_CALLS}).\n"
            f"Revisa los errores y corrígelos antes de terminar:\n\n"
            f"{test_result.get('output', '')}"
        )
        print(json.dumps({
            "decision": "continue",
            "reason":   reason,
        }, ensure_ascii=False))
        sys.exit(0)


if __name__ == "__main__":
    main()
