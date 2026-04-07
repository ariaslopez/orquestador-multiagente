"""
Hooks de Lifecycle — Fase 12

Scripts que se ejecutan en puntos clave del ciclo del agente.
Inspiration: Claude Code hooks system (PreToolUse, PostToolUse, Stop, SessionStart, UserPromptSubmit)

Cada hook recibe JSON por stdin y puede:
  - Salir con exit code 0: acción permitida, continuar
  - Salir con exit code 2: BLOQUEAR la acción
  - Imprimir JSON con "decision": "continue": FORZAR al agente a seguir iterando

Hooks disponibles:
  session-start.py      - Inyecta CLAW.md + skills al iniciar sesión
  pretool-guard.py      - Enforcea workspace boundaries antes de Write/Bash
  posttool-validate.py  - Corre lint+tests despues de escritura
  stop-enforcer.py      - Fuerza iteración si tests fallan (reemplaza loop manual)
"""
