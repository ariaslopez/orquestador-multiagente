"""
orchestrator.py — Tombstone de compatibilidad (v2.2.2)

REEMPLAZADO por: core.maestro.Maestro

Este módulo existe solo para que imports legacy no rompan.
NO usar en código nuevo.

Migración:
    # Antes
    from core.orchestrator import Orchestrator
    orch = Orchestrator()

    # Ahora
    from core.maestro import Maestro
    maestro = Maestro()
    result = await maestro.run(user_input="...")
"""
from core.maestro import Maestro as Orchestrator  # alias de compatibilidad

__all__ = ["Orchestrator"]
