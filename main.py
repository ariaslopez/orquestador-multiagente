"""CLAW Agent System — Punto de entrada principal."""
import os
import sys
import asyncio
import argparse
import subprocess
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env antes que todo
load_dotenv()

VERSION = "2.0.0"

ALL_PIPELINES = [
    "dev", "research", "content", "office", "qa", "pm", "trading",
    "analytics", "marketing", "product", "security_audit", "design",
]


def check_setup() -> bool:
    """Verifica que el sistema está configurado. Si no, ejecuta setup."""
    env_file = Path(".env")
    if not env_file.exists():
        print("\n⚠️  No se encontró el archivo .env")
        print("   Ejecuta primero: python setup.py\n")
        return False
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key or groq_key == "your_groq_api_key_here":
        print("\n⚠️  GROQ_API_KEY no configurada en .env")
        print("   Ejecuta: python setup.py\n")
        return False
    return True


def run_doctor() -> None:
    """Verifica el estado de todas las dependencias y APIs."""
    from rich.console import Console
    from rich.table import Table
    console = Console()
    console.print(f"\n[bold cyan]👨‍⚕️  CLAW Doctor v{VERSION} — Verificando sistema...[/bold cyan]\n")

    checks = []

    # Python version
    py_ver = sys.version_info
    checks.append(("Python 3.10+", py_ver >= (3, 10), f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"))

    # .env
    checks.append((".env existe", Path(".env").exists(), ""))

    # APIs
    for api, key_env in [
        ("Groq", "GROQ_API_KEY"),
        ("Gemini", "GEMINI_API_KEY"),
        ("Supabase URL", "SUPABASE_URL"),
        ("GitHub Token", "GITHUB_TOKEN"),
    ]:
        val = os.getenv(key_env, "")
        ok = bool(val) and "your_" not in val
        checks.append((f"{api} API Key", ok, "✅" if ok else "❌ no configurada"))

    # Packages
    for pkg in [
        "groq", "fastapi", "uvicorn", "supabase", "rich",
        "duckduckgo_search", "github", "yaml", "aiohttp",
    ]:
        try:
            __import__(pkg.replace("-", "_"))
            checks.append((f"pkg: {pkg}", True, "✅ instalado"))
        except ImportError:
            checks.append((f"pkg: {pkg}", False, "❌ falta — ejecuta: pip install -r requirements.txt"))

    # Pipelines (12)
    checks.append(("Pipelines registrados", True, f"{len(ALL_PIPELINES)}/12 ✅"))

    table = Table(title=f"Estado del Sistema — CLAW v{VERSION}", show_header=True)
    table.add_column("Componente", style="cyan")
    table.add_column("Estado", style="bold")
    table.add_column("Detalle")

    all_ok = True
    for name, ok, detail in checks:
        status = "[green]✅ OK[/green]" if ok else "[red]❌ FALLO[/red]"
        if not ok:
            all_ok = False
        table.add_row(name, status, detail)

    console.print(table)
    if all_ok:
        console.print("\n[bold green]✅ Todo en orden — el sistema está listo para usar.[/bold green]\n")
    else:
        console.print("\n[bold yellow]⚠️  Algunos componentes necesitan atención. Revisa los ❌ arriba.[/bold yellow]\n")


async def run_task(
    task: str,
    task_type: str = None,
    input_file: str = None,
    input_repo: str = None,
    output_path: str = None,
    verbose: bool = False,
    auto: bool = False,
) -> None:
    """Ejecuta una tarea a través del Maestro."""
    from rich.console import Console
    from rich.panel import Panel
    from infrastructure.memory_manager import MemoryManager
    from core.maestro import Maestro

    console = Console()
    memory = MemoryManager()
    maestro = Maestro(memory_manager=memory)

    console.print(f"\n[bold cyan]🧠 CLAW Agent System v{VERSION}[/bold cyan]")
    console.print(f"   Tarea: [white]{task}[/white]")
    if task_type:
        console.print(f"   Pipeline forzado: [yellow]{task_type}[/yellow]")
    console.print()

    with console.status("[cyan]Clasificando tarea y preparando pipeline...[/cyan]"):
        ctx = await maestro.run(
            user_input=task,
            task_type=task_type,
            input_file=input_file,
            input_repo=input_repo,
            output_path=output_path,
            auto_mode=auto,
        )

    console.print(Panel(
        ctx.final_output or "(Sin output generado)",
        title=f"[bold green]✅ Completado — Pipeline: {ctx.pipeline_name}[/bold green]",
        border_style="green",
    ))

    console.print(
        f"\n[dim]⏱️  {ctx.duration_seconds:.1f}s  |  "
        f"🔢 {ctx.total_tokens:,} tokens  |  "
        f"💰 ${ctx.estimated_cost_usd:.4f} USD  |  "
        f"💾 Sesión: {ctx.session_id[:8]}[/dim]"
    )

    if ctx.output_path:
        console.print(f"[dim]📁 Output guardado en: {ctx.output_path}[/dim]\n")

    if verbose:
        console.print("\n[bold yellow]--- Logs detallados por agente ---[/bold yellow]")
        for agent_name, logs in ctx.agent_logs.items():
            console.print(f"\n[cyan]{agent_name}:[/cyan]")
            for entry in logs:
                console.print(f"  [dim]{entry}[/dim]")


def run_interactive() -> None:
    """Modo interactivo en terminal: loop de preguntas continuo."""
    from rich.console import Console
    from rich.prompt import Prompt
    console = Console()

    console.print(f"\n[bold cyan]🧠 CLAW Agent System v{VERSION} — Modo Interactivo[/bold cyan]")
    console.print("[dim]Escribe tu tarea en lenguaje natural. 'salir' para terminar.[/dim]\n")

    while True:
        try:
            task = Prompt.ask("[bold green]💬 Tarea[/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Hasta luego.[/yellow]\n")
            break

        if task.lower() in ("salir", "exit", "quit", "q"):
            console.print("[yellow]Hasta luego.[/yellow]\n")
            break
        if not task:
            continue

        asyncio.run(run_task(task))


def run_ui() -> None:
    """Inicia el dashboard web."""
    from ui.server import start_server
    auto_open = os.getenv("UI_AUTO_OPEN", "true").lower() == "true"
    host = os.getenv("UI_HOST", "127.0.0.1")
    port = int(os.getenv("UI_PORT", "8000"))

    if auto_open:
        webbrowser.open(f"http://{host}:{port}")

    start_server(host=host, port=port)


def main():
    parser = argparse.ArgumentParser(
        prog="claw",
        description=f"🧠 CLAW Agent System v{VERSION} — Orquestador autónomo multi-agente (12 pipelines)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Pipelines disponibles: {', '.join(ALL_PIPELINES)}

Ejemplos:
  python main.py --task "Crea un bot de trading para BTC/USDT"
  python main.py --task "Analiza este Excel" --file data.xlsx --type office
  python main.py --task "Plan de marketing para SaaS B2B" --type marketing
  python main.py --task "Audita seguridad de esta API" --type security_audit
  python main.py --task "Tesis de inversion para SOL" --type research
  python main.py --interactive
  python main.py --ui
  python main.py --doctor
        """,
    )

    # Acciones principales
    parser.add_argument("--task", "-t", type=str, help="Tarea a ejecutar en lenguaje natural")
    parser.add_argument("--interactive", "-i", action="store_true", help="Modo interactivo (loop de tareas)")
    parser.add_argument("--ui", action="store_true", help="Iniciar dashboard web")
    parser.add_argument("--doctor", action="store_true", help="Verificar estado del sistema")
    parser.add_argument("--setup", action="store_true", help="Ejecutar configuración inicial")

    # Opciones de tarea — 12 pipelines
    parser.add_argument(
        "--type",
        choices=ALL_PIPELINES,
        metavar="PIPELINE",
        help=f"Forzar tipo de pipeline. Opciones: {', '.join(ALL_PIPELINES)}",
    )
    parser.add_argument("--file", "-f", type=str, help="Archivo de entrada (.xlsx, .pdf, .docx, etc.)")
    parser.add_argument("--repo", "-r", type=str, help="Repositorio GitHub (owner/repo)")
    parser.add_argument("--output", "-o", type=str, help="Carpeta de output")

    # Modificadores
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar logs detallados de cada agente")
    parser.add_argument("--auto", "-a", action="store_true", help="Modo automático sin confirmaciones")
    parser.add_argument("--env", choices=["local", "server"], help="Forzar ambiente (sobreescribe .env)")

    # Info
    parser.add_argument("--history", action="store_true", help="Ver historial de sesiones")
    parser.add_argument("--usage", action="store_true", help="Ver estadísticas de uso y costos")
    parser.add_argument("--version", action="store_true", help="Ver versión del sistema")

    args = parser.parse_args()

    if args.env:
        os.environ["CLAW_ENV"] = args.env

    # Acciones que no requieren setup
    if args.version:
        print(f"CLAW Agent System v{VERSION}")
        return
    if args.doctor:
        run_doctor()
        return
    if args.setup:
        subprocess.run([sys.executable, 'setup.py'], check=False)
        return

    # Verificar setup para el resto de acciones
    if not check_setup():
        sys.exit(1)

    if args.history:
        from infrastructure.memory_manager import MemoryManager
        from rich.console import Console
        from rich.table import Table
        memory = MemoryManager()
        sessions = memory.get_all_sessions(limit=20)
        console = Console()
        table = Table(title="Historial de Sesiones (20 últimas)")
        table.add_column("ID", style="dim", width=10)
        table.add_column("Tarea", max_width=40)
        table.add_column("Tipo")
        table.add_column("Estado")
        table.add_column("Tokens")
        table.add_column("Fecha")
        for s in sessions:
            table.add_row(
                s["session_id"][:8],
                s["user_input"][:40],
                s["task_type"],
                s["status"],
                str(s.get("total_tokens", 0)),
                s["created_at"][:16] if s.get("created_at") else "",
            )
        console.print(table)
        return

    if args.usage:
        from infrastructure.memory_manager import MemoryManager
        from rich.console import Console
        memory = MemoryManager()
        stats = memory.get_usage_stats()
        console = Console()
        console.print("\n[bold cyan]📊 Estadísticas de Uso[/bold cyan]")
        console.print(f"  Total sesiones: [white]{stats.get('total_sessions', 0)}[/white]")
        console.print(f"  Total tokens:   [white]{stats.get('total_tokens', 0):,}[/white]")
        console.print(f"  Costo total:    [white]${stats.get('total_cost_usd', 0):.4f} USD[/white]")
        console.print(f"  Duración prom:  [white]{stats.get('avg_duration', 0):.1f}s[/white]\n")
        return

    if args.ui:
        run_ui()
        return

    if args.interactive:
        run_interactive()
        return

    if args.task:
        asyncio.run(run_task(
            task=args.task,
            task_type=args.type,
            input_file=args.file,
            input_repo=args.repo,
            output_path=args.output,
            verbose=args.verbose,
            auto=args.auto,
        ))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
