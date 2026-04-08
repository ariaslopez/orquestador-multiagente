"""
pipeline.py — Tombstone de compatibilidad (v2.2.2)

REEMPLAZADO por: core.pipeline_router.PipelineRouter

Este módulo existe solo para que imports legacy no rompan.
NO usar en código nuevo.

Migración:
    # Antes
    from core.pipeline import Pipeline

    # Ahora
    from core.pipeline_router import PipelineRouter
"""
from core.pipeline_router import PipelineRouter as Pipeline  # alias de compatibilidad

__all__ = ["Pipeline"]
