"""
orchestrator.py — Tombstone de compatibilidad (v2.2.2 → PR-2)

REEMPLAZADO por: core.maestro.Maestro

Este módulo emite DeprecationWarning en el momento del import y será
eliminado en PR-3. NO usar en código nuevo.

Migración:
    # Antes
    from core.orchestrator import Orchestrator
    orch = Orchestrator()

    # Ahora
    from core.maestro import Maestro
    maestro = Maestro()
    result = await maestro.run(user_input="...")
"""
import warnings

warnings.warn(
    "core.orchestrator está deprecado y será eliminado en PR-3. "
    "Usa: from core.maestro import Maestro",
    DeprecationWarning,
    stacklevel=2,
)

from core.maestro import Maestro as Orchestrator  # alias de compatibilidad

__all__ = ["Orchestrator"]
