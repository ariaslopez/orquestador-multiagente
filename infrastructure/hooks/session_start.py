#!/usr/bin/env python3
"""
Hook: SessionStart
Se ejecuta al inicio de cada sesión del agente.

Responsabilidades:
  1. Detectar si existe CLAW.md en el workspace
  2. Si no existe, notificar al agente para que lo genere
  3. Cargar skills del proyecto (.claw/skills/) e inyectarlos en contexto
  4. Loguear inicio de sesión con metadata
"""

import json
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [session-start] %(message)s")
logger = logging.getLogger(__name__)


def load_claw_context(workspace: Path) -> dict:
    """Carga CLAW.md y enumera los skills disponibles."""
    context = {"claw_md": None, "skills": [], "commands": []}

    claw_path = workspace / "CLAW.md"
    if claw_path.exists():
        context["claw_md"] = claw_path.read_text(encoding="utf-8")
        logger.info(f"CLAW.md cargado ({len(context['claw_md'])} chars)")
    else:
        logger.warning("CLAW.md no encontrado — ejecuta: python main.py --init .")

    # Skills formato nuevo: .claw/skills/<name>/SKILL.md
    skills_dir = workspace / ".claw" / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                context["skills"].append({
                    "name":    skill_dir.name,
                    "path":    str(skill_file),
                    "content": skill_file.read_text(encoding="utf-8")[:500],  # preview
                })
        logger.info(f"{len(context['skills'])} skills cargados")

    # Commands formato legacy: .claw/commands/*.md
    commands_dir = workspace / ".claw" / "commands"
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            context["commands"].append({
                "name":    cmd_file.stem,
                "path":    str(cmd_file),
                "content": cmd_file.read_text(encoding="utf-8")[:500],
            })
        logger.info(f"{len(context['commands'])} commands legacy cargados")

    return context


def main():
    workspace = Path(os.getenv("CLAW_WORKSPACE", ".")).resolve()
    session_id = os.getenv("CLAW_SESSION_ID", "unknown")

    logger.info(f"Sesión iniciada | workspace={workspace} | session={session_id}")

    ctx = load_claw_context(workspace)

    output = {
        "session_id":    session_id,
        "workspace":     str(workspace),
        "claw_md_found": ctx["claw_md"] is not None,
        "skills_count":  len(ctx["skills"]),
        "skills":        [s["name"] for s in ctx["skills"]],
        "commands_count": len(ctx["commands"]),
    }

    if not ctx["claw_md"]:
        output["suggestion"] = (
            "CLAW.md no encontrado. Ejecuta 'python main.py --init .' "
            "para generar el contexto del proyecto."
        )

    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
