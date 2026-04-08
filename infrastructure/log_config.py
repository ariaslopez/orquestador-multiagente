"""CLAW — Configuración centralizada de logging.

Uso:
    from infrastructure.log_config import setup_logging
    setup_logging()   # llamar una sola vez al inicio (main.py)

Después de llamar setup_logging(), cualquier módulo que haga:
    logger = logging.getLogger(__name__)
    logger.info("...")

automáticamente escribe en:
  - Consola (Rich, coloreado)
  - data/claw.log (archivo rotativo, max 5MB x 3 backups)

Niveles configurables en .env:
  LOG_LEVEL=DEBUG     → todo (verboso, para desarrollo)
  LOG_LEVEL=INFO      → flujo normal del sistema (default)
  LOG_LEVEL=WARNING   → solo advertencias y errores
  LOG_LEVEL=ERROR     → solo errores criticos

Formato en archivo:
  2026-04-07 19:05:42 | INFO     | core.maestro         | Maestro.run() | task_type=dev
  2026-04-07 19:05:43 | WARNING  | infrastructure.memory| Supabase sync fallo: ...
  2026-04-07 19:05:44 | ERROR    | core.base_agent      | PlannerAgent Error: ...
"""
from __future__ import annotations
import os
import logging
import logging.handlers
from pathlib import Path

# Ruta del log consolidado
LOG_DIR  = Path(os.getenv("LOG_PATH", "data"))
LOG_FILE = LOG_DIR / "claw.log"

# Formato unificado para archivo
FILE_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s"
)
FILE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Formato corto para consola
CONSOLE_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
CONSOLE_DATE_FORMAT = "%H:%M:%S"

# Modulos muy verbosos que bajamos a WARNING para no contaminar los logs
_NOISY_LOGGERS = [
    "httpx", "httpcore", "urllib3", "asyncio",
    "openai", "groq", "supabase", "hpack",
    "multipart", "uvicorn.access",
]


def setup_logging(level: str = None) -> None:
    """
    Configura el sistema de logging centralizado de CLAW.
    Debe llamarse UNA sola vez al inicio de main.py.

    Args:
        level: Nivel de log. Si None, lee LOG_LEVEL del .env (default: INFO).
    """
    raw_level = level or os.getenv("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, raw_level.upper(), logging.INFO)

    # Crear directorio si no existe
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Root logger
    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Evitar agregar handlers multiples si se llama mas de una vez
    if root.handlers:
        return

    # ------------------------------------------------------------------
    # Handler 1: Archivo rotativo (data/claw.log)
    # 5 MB por archivo, maximo 3 backups = 15 MB total
    # ------------------------------------------------------------------
    file_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(
        logging.Formatter(fmt=FILE_FORMAT, datefmt=FILE_DATE_FORMAT)
    )

    # ------------------------------------------------------------------
    # Handler 2: Consola con Rich (coloreado)
    # ------------------------------------------------------------------
    try:
        from rich.logging import RichHandler
        console_handler = RichHandler(
            level=numeric_level,
            show_time=True,
            show_level=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
    except ImportError:
        # Fallback a handler estandar si Rich no esta instalado
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(
            logging.Formatter(fmt=CONSOLE_FORMAT, datefmt=CONSOLE_DATE_FORMAT)
        )

    # Registrar handlers en root
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # ------------------------------------------------------------------
    # Silenciar librerias de terceros ruidosas
    # ------------------------------------------------------------------
    for noisy in _NOISY_LOGGERS:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Primer mensaje del sistema
    logger = logging.getLogger("claw.boot")
    logger.info(
        f"CLAW logging iniciado | nivel={raw_level} | archivo={LOG_FILE}"
    )


def get_log_path() -> Path:
    """Retorna la ruta del archivo de log consolidado."""
    return LOG_FILE
