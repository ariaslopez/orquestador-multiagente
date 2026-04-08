"""agents/shared — utilidades transversales reutilizables por cualquier pipeline.

Agentes en este módulo NO pertenecen a un pipeline específico.
Son componentes de soporte que pueden ser etapas opcionales de cualquier pipeline.

Contenido actual:
  - ResponseAgent: consolida el output de todos los agentes anteriores
    y formatea la respuesta final al usuario. Migrado de agents/response_agent.py
    (v1) en PR-2.
"""
from .response_agent import ResponseAgent

__all__ = ["ResponseAgent"]
