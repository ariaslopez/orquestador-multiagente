#!/usr/bin/env python3
"""
CLAW Agent System — Script de configuración de entorno virtual.

Uso:
    python scripts/setup_venv.py              # crea venv + instala deps
    python scripts/setup_venv.py --verify     # solo verifica imports
    python scripts/setup_venv.py --clean      # elimina venv y recrea

El script:
  1. Crea .venv/ en la raíz del proyecto
  2. Instala todas las dependencias de requirements.txt
  3. Verifica que todos los imports críticos funcionan
  4. Crea .env desde .env.example si no existe
  5. Corre python main.py --doctor al final
"""
from __future__ import annotations
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Raíz del proyecto = directorio padre de scripts/
ROOT = Path(__file__).parent.parent.resolve()
VENV = ROOT / ".venv"

# Detectar ejecutable de python en el venv
if sys.platform == "win32":
    VENV_PYTHON = VENV / "Scripts" / "python.exe"
    VENV_PIP    = VENV / "Scripts" / "pip.exe"
else:
    VENV_PYTHON = VENV / "bin" / "python"
    VENV_PIP    = VENV / "bin" / "pip"


def run(cmd: list, check: bool = True, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    """Ejecuta un comando y muestra output en tiempo real."""
    print(f"\n▶ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=check, cwd=cwd)


def print_header(title: str) -> None:
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def create_venv() -> None:
    print_header("1/5 — Creando entorno virtual")
    if VENV.exists():
        print(f"✅  .venv ya existe en {VENV}")
        return
    run([sys.executable, "-m", "venv", str(VENV)])
    print(f"✅  Entorno virtual creado en {VENV}")


def install_deps() -> None:
    print_header("2/5 — Instalando dependencias")
    req = ROOT / "requirements.txt"
    if not req.exists():
        print(f"❌  No se encontró requirements.txt en {ROOT}")
        sys.exit(1)

    # Actualizar pip primero
    run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"])
    # Instalar dependencias
    run([str(VENV_PIP), "install", "-r", str(req)])
    print("✅  Dependencias instaladas")


def verify_imports() -> None:
    print_header("3/5 — Verificando imports críticos")

    critical = [
        ("fastapi",           "FastAPI"),
        ("uvicorn",           "uvicorn"),
        ("groq",              "Groq SDK"),
        ("openai",            "OpenAI SDK"),
        ("google.generativeai", "Gemini SDK"),
        ("rich",              "Rich"),
        ("dotenv",            "python-dotenv"),
        ("aiohttp",           "aiohttp"),
        ("yaml",              "PyYAML"),
    ]

    optional = [
        ("supabase",           "Supabase"),
        ("github",             "PyGithub"),
        ("duckduckgo_search",  "DuckDuckGo Search"),
        ("sentence_transformers", "sentence-transformers"),
    ]

    failed_critical = []
    failed_optional = []

    for module, label in critical:
        try:
            result = subprocess.run(
                [str(VENV_PYTHON), "-c", f"import {module}; print('{label} OK')"],
                capture_output=True, text=True, cwd=ROOT,
            )
            if result.returncode == 0:
                print(f"  ✅  {label}")
            else:
                print(f"  ❌  {label} — {result.stderr.strip()[:60]}")
                failed_critical.append(label)
        except Exception as e:
            print(f"  ❌  {label} — {e}")
            failed_critical.append(label)

    for module, label in optional:
        try:
            result = subprocess.run(
                [str(VENV_PYTHON), "-c", f"import {module}; print('{label} OK')"],
                capture_output=True, text=True, cwd=ROOT,
            )
            status = "✅" if result.returncode == 0 else "⚠️ (opcional)"
            print(f"  {status}  {label}")
            if result.returncode != 0:
                failed_optional.append(label)
        except Exception:
            print(f"  ⚠️ (opcional)  {label}")
            failed_optional.append(label)

    if failed_critical:
        print(f"\n❌  Imports críticos fallaron: {failed_critical}")
        print("   Ejecuta: pip install -r requirements.txt")
        sys.exit(1)

    if failed_optional:
        print(f"\n⚠️  Imports opcionales no disponibles: {failed_optional}")
        print("   No bloquean el sistema pero reducen funcionalidad.")

    print("✅  Todos los imports críticos OK")


def setup_env() -> None:
    print_header("4/5 — Configurando .env")
    env_file     = ROOT / ".env"
    env_example  = ROOT / ".env.example"

    if env_file.exists():
        print(f"✅  .env ya existe en {env_file}")
        return

    if env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"✅  .env creado desde .env.example")
        print("⚠️  Edita .env y configura al menos una de estas opciones:")
        print("     A) GROQ_API_KEY=tu_key  (https://console.groq.com, gratis)")
        print("     B) OLLAMA_ENABLED=true  (requiere ollama instalado)")
    else:
        # Crear .env mínimo
        minimal_env = """# CLAW Agent System — Configuración mínima
# Opción A: Groq (cloud, gratis) — https://console.groq.com
GROQ_API_KEY=

# Opción B: Ollama (local, gratis) — https://ollama.com
OLLAMA_ENABLED=false
OLLAMA_HW_PROFILE=cpu_24gb
OLLAMA_BASE_URL=http://localhost:11434/v1

# Gemini (fallback, gratis) — https://aistudio.google.com
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# Sistema
CLAW_ENV=local
LOG_LEVEL=INFO
OUTPUT_PATH=./output
MAX_LOOP_ITERATIONS=5
LLM_TIMEOUT_SECONDS=45
API_STRATEGY=local_first
"""
        env_file.write_text(minimal_env)
        print(f"✅  .env mínimo creado en {env_file}")
        print("⚠️  Edita .env y agrega tus API keys antes de usar el sistema")


def run_doctor() -> None:
    print_header("5/5 — Verificando sistema (--doctor)")
    result = subprocess.run(
        [str(VENV_PYTHON), "main.py", "--doctor"],
        cwd=ROOT, check=False,
    )
    if result.returncode != 0:
        print("⚠️  --doctor reportó advertencias (ver arriba)")


def clean_venv() -> None:
    print_header("Limpiando entorno virtual")
    if VENV.exists():
        shutil.rmtree(VENV)
        print(f"✅  .venv eliminado")
    else:
        print("⚠️  .venv no existe, nada que limpiar")


def print_activation_hint() -> None:
    print_header("✅ Entorno listo")
    if sys.platform == "win32":
        activate = r".venv\Scripts\activate"
    else:
        activate = "source .venv/bin/activate"

    print(f"""
Activa el entorno virtual con:
  {activate}

Comandos disponibles:
  python main.py --doctor
  python main.py --task "Crea un bot RSI para XAUUSD" --auto
  python main.py --task "Audita seguridad de la API" --plan
  python main.py --interactive

Version: 2.2.1
""")


def main():
    parser = argparse.ArgumentParser(
        description="CLAW — Setup de entorno virtual"
    )
    parser.add_argument("--verify", action="store_true", help="Solo verificar imports")
    parser.add_argument("--clean",  action="store_true", help="Eliminar venv y recrear")
    args = parser.parse_args()

    print(f"""
╔{'=' * 58}╗
║  CLAW Agent System v2.2.1 — Setup de entorno virtual        ║
╔{'=' * 58}╗
    """)

    if args.verify:
        verify_imports()
        return

    if args.clean:
        clean_venv()

    create_venv()
    install_deps()
    verify_imports()
    setup_env()
    run_doctor()
    print_activation_hint()


if __name__ == "__main__":
    main()
