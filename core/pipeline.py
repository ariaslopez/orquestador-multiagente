"""
pipeline.py — Tombstone de compatibilidad (v2.2.2 → PR-2)

REEMPLAZADO por: core.pipeline_router.PipelineRouter

Este módulo emite DeprecationWarning en el momento del import y será
eliminado en PR-3. NO usar en código nuevo.

Migración:
    # Antes
    from core.pipeline import Pipeline

    # Ahora
    from core.pipeline_router import PipelineRouter
"""
import warnings

warnings.warn(
    "core.pipeline está deprecado y será eliminado en PR-3. "
    "Usa: from core.pipeline_router import PipelineRouter",
    DeprecationWarning,
    stacklevel=2,
)

from core.pipeline_router import PipelineRouter as Pipeline  # alias de compatibilidad

__all__ = ["Pipeline"]
