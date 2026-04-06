"""Registro de personalidades especializadas — loader sobre config/personas.yaml.

Se carga una sola vez al importar el modulo (lazy singleton).
Para agregar o editar personas, edita config/personas.yaml — no este archivo.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

import yaml

_PERSONAS_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "personas.yaml"


@lru_cache(maxsize=1)
def _load_personas() -> Dict[str, dict]:
    """Carga y cachea el YAML de personas."""
    with open(_PERSONAS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


# Alias publico para compatibilidad retroactiva con imports existentes
PERSONAS: Dict[str, dict] = _load_personas()


def get_persona(name: str) -> Optional[dict]:
    """Obtiene una persona por nombre. Case-insensitive."""
    key = name.lower().replace(" ", "_").replace("-", "_")
    return _load_personas().get(key)


def list_personas(division: Optional[str] = None) -> list[str]:
    """Lista nombres de personas, opcionalmente filtradas por division."""
    personas = _load_personas()
    if division:
        return [k for k, v in personas.items() if v.get("division", "").lower() == division.lower()]
    return list(personas.keys())


def get_persona_prompt(name: str) -> str:
    """Retorna el system prompt completo para una persona."""
    p = get_persona(name)
    if not p:
        return ""
    workflow_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(p.get("workflow", [])))
    deliverables_str = "\n".join(f"- {d}" for d in p.get("deliverables", []))
    return f"""{p['identity']}

MISION: {p['mission']}

WORKFLOW:
{workflow_str}

ENTREGABLES ESPERADOS:
{deliverables_str}

TONO: {p.get('tone', '')}"""
