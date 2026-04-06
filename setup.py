"""CLAW Agent System — Instalador interactivo."""
import os
import sys
import subprocess
from pathlib import Path


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def ask(prompt: str, default: str = "", secret: bool = False) -> str:
    """Pregunta al usuario con valor por defecto."""
    display = f"{prompt}"
    if default:
        display += f" [{default}]"
    display += ": "
    try:
        if secret:
            import getpass
            val = getpass.getpass(display)
        else:
            val = input(display).strip()
        return val if val else default
    except (KeyboardInterrupt, EOFError):
        print("\n\nInstalación cancelada.")
        sys.exit(0)


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    default_str = "S/n" if default else "s/N"
    val = ask(f"{prompt} ({default_str})").lower()
    if not val:
        return default
    return val in ("s", "si", "yes", "y")


def install_requirements():
    print("\n📦 Instalando dependencias...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("   ✅ Dependencias instaladas")
    else:
        print(f"   ⚠️  Advertencia: {result.stderr[:200]}")


def main():
    clear()
    print("""

 ╭──────────────────────────────────╮
 │   🧠  CLAW Agent System v1.0.0      │
 │   Configuración inicial              │
 ╰──────────────────────────────────╯
""")
    print("Este asistente te guiará paso a paso.")
    print("Puedes presionar Enter para aceptar los valores por defecto.\n")

    # ----------------------------------------------------------------
    # PASO 1 — Ambiente
    # ----------------------------------------------------------------
    print("\n🔧 PASO 1 — ¿En qué ambiente correrá el sistema?")
    print("   1) local  — tu PC personal (desarrollo)")
    print("   2) server — servidor cloud / Windows Server (producción)")
    env_choice = ask("Elige [1/2]", default="1")
    claw_env = "server" if env_choice == "2" else "local"
    print(f"   ✅ Ambiente: {claw_env}")

    # ----------------------------------------------------------------
    # PASO 2 — Carpeta de output
    # ----------------------------------------------------------------
    print("\n📁 PASO 2 — ¿Dónde guardar los resultados?")
    print("   Esta carpeta contendrá todos los proyectos y reportes generados.")
    if os.name == "nt":  # Windows
        default_output = "C:/CLAW_Output"
        print("   Ejemplos: C:/CLAW_Output | D:/Projects/claw_output")
    else:  # Linux / Mac
        default_output = str(Path.home() / "claw_output")
        print(f"   Ejemplo: {default_output}")

    output_path = ask("Ruta de output", default=default_output)
    output_path = output_path.replace("\\", "/")

    # Crear carpeta
    try:
        Path(output_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Carpeta creada/verificada: {output_path}")
    except Exception as e:
        print(f"   ⚠️  No se pudo crear la carpeta: {e}")
        output_path = "./output"
        print(f"   • Usando carpeta local por defecto: {output_path}")

    # ----------------------------------------------------------------
    # PASO 3 — API Keys
    # ----------------------------------------------------------------
    print("\n🔑 PASO 3 — API Keys")
    print("   Necesitas al menos Groq para que el sistema funcione.")
    print("   Groq es gratis: https://console.groq.com\n")

    groq_key = ask("   Groq API Key", secret=True)
    while not groq_key:
        print("   ❌ La Groq API Key es obligatoria.")
        groq_key = ask("   Groq API Key", secret=True)

    print("\n   Google Gemini (opcional, gratis): https://aistudio.google.com")
    gemini_key = ask("   Gemini API Key (Enter para omitir)", secret=True)

    print("\n   GitHub Token (opcional — para modificar repos):")
    print("   Obtener en: GitHub > Settings > Developer settings > Personal access tokens")
    github_token = ask("   GitHub Token (Enter para omitir)", secret=True)

    print("\n   Supabase (opcional — para memoria entre sesiones/máquinas):")
    print("   Obtener en: https://supabase.com > Settings > API")
    supabase_url = ask("   Supabase URL (Enter para omitir)")
    supabase_key = ""
    if supabase_url:
        supabase_key = ask("   Supabase Anon Key", secret=True)

    # ----------------------------------------------------------------
    # PASO 4 — UI
    # ----------------------------------------------------------------
    print("\n🌐 PASO 4 — Dashboard Web")
    ui_port = ask("   Puerto del dashboard", default="8000")
    ui_auto_open = ask_yes_no("   ¿Abrir el browser automáticamente al iniciar?", default=True)

    # ----------------------------------------------------------------
    # PASO 5 — Instalar dependencias
    # ----------------------------------------------------------------
    print("\n📦 PASO 5 — Dependencias")
    install_deps = ask_yes_no("   ¿Instalar dependencias ahora (pip install -r requirements.txt)?", default=True)
    if install_deps:
        install_requirements()

    # ----------------------------------------------------------------
    # GENERAR .env
    # ----------------------------------------------------------------
    print("\n📝 Generando archivo .env...")

    env_content = f"""# CLAW Agent System — Generado por setup.py
# Creado: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Ambiente
CLAW_ENV={claw_env}

# LLM APIs
GROQ_API_KEY={groq_key}
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_MODEL_FAST=llama-3.1-8b-instant
GEMINI_API_KEY={gemini_key}
GEMINI_MODEL=gemini-2.0-flash
HYPERSPACE_BASE_URL=http://localhost:8080/v1
HYPERSPACE_ENABLED=false

# Supabase
SUPABASE_URL={supabase_url}
SUPABASE_KEY={supabase_key}

# GitHub
GITHUB_TOKEN={github_token}
GITHUB_USERNAME=
GITHUB_PROTECTED_BRANCHES=main,master,production
GITHUB_AUTO_PR=true
GITHUB_CONFIRM_BEFORE_PUSH=true

# Rutas
OUTPUT_PATH={output_path}
LOGS_PATH={output_path}/logs

# UI Dashboard
UI_HOST=127.0.0.1
UI_PORT={ui_port}
UI_AUTO_OPEN={'true' if ui_auto_open else 'false'}

# Seguridad
ALLOWED_DOMAINS=api.groq.com,generativelanguage.googleapis.com,api.github.com,supabase.co,api.coingecko.com,api.llama.fi,duckduckgo.com,pypi.org,npmjs.com
MAX_AGENT_RETRIES=3

# Logging
LOG_LEVEL=INFO
AGENT_VERBOSE_LOGS=false
"""

    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)

    print("   ✅ Archivo .env creado")

    # ----------------------------------------------------------------
    # FINALIZAR
    # ----------------------------------------------------------------
    print("""

 ╭──────────────────────────────────╮
 │   ✅  Configuración completada!        │
 ╰──────────────────────────────────╯

 Próximos pasos:
""")
    print("  1️⃣  Verificar sistema:   python main.py --doctor")
    print("  2️⃣  Modo interactivo:   python main.py --interactive")
    print("  3️⃣  Dashboard web:      python main.py --ui")
    print("  4️⃣  Ejecutar tarea:     python main.py --task \"tu tarea\"\n")


if __name__ == "__main__":
    main()
