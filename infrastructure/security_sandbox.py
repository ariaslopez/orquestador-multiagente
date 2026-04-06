"""SecuritySandbox — Clase canonica de seguridad del sistema CLAW.

Cubre 5 capas:
  1. Path Validation   — bloquea rutas del sistema y credenciales
  2. Command Whitelist — solo comandos explicitamente permitidos
  3. Network Audit     — verifica dominios autorizados
  4. Secrets Detection — escanea y redacta secretos en outputs
  5. Audit Log         — registra TODA operacion de seguridad
"""
from __future__ import annotations
import os
import re
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SecuritySandbox:
    """
    Instancia con log_path opcional (default: ./logs).
    Usada por CodeExecutorTool y SecurityAgent.
    """

    PROTECTED_PATHS = [
        # Sistema operativo — Linux
        "/etc", "/sys", "/proc", "/boot", "/root",
        "/bin", "/sbin", "/usr/bin", "/usr/sbin",
        "/var/run",
        # macOS — FIX: agregado para cubrir rutas de usuario y sistema en Mac
        "/Users",
        "/Library",
        "/System",
        "/private/etc",
        # Windows
        "C:/Windows", "C:/System32", "C:/Program Files",
        "C:\\Windows", "C:\\System32", "C:\\Program Files",
        # Credenciales de usuario (todos los OS)
        os.path.expanduser("~/.ssh"),
        os.path.expanduser("~/.aws"),
        os.path.expanduser("~/.gnupg"),
        os.path.expanduser("~/.config"),
        os.path.expanduser("~/.local"),
    ]

    ALLOWED_COMMANDS = [
        "pip install", "pip3 install", "pip uninstall",
        "npm install", "npm run",
        "yarn install",
        "python", "python3",
        "node", "npx",
        "cargo build", "cargo run",
        "go build", "go run", "go mod tidy",
        "pytest", "jest", "unittest",
        "git clone", "git add", "git commit", "git push",
        "git checkout", "git pull", "git branch",
        "mkdir", "touch", "cp", "mv",
    ]

    BLOCKED_PATTERNS = [
        r"rm\s+-rf", r"rmdir\s+/s", r"del\s+/f",
        r"format\s+[a-zA-Z]:",
        r"DROP\s+TABLE", r"DROP\s+DATABASE", r"TRUNCATE",
        r"shutdown", r"reboot", r"halt",
        r"chmod\s+777", r"chown\s+root",
        r"curl.*\|.*bash", r"wget.*\|.*sh",
    ]

    SECRET_PATTERNS = [
        r"[Aa][Pp][Ii][_]?[Kk][Ee][Yy]\s*=\s*['\"][^'\"]{10,}",
        r"[Ss][Ee][Cc][Rr][Ee][Tt]\s*=\s*['\"][^'\"]{10,}",
        r"[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]\s*=\s*['\"][^'\"]{8,}",
        r"[Tt][Oo][Kk][Ee][Nn]\s*=\s*['\"][^'\"]{10,}",
        r"ghp_[a-zA-Z0-9]{36}",    # GitHub personal token
        r"gsk_[a-zA-Z0-9]{52}",    # Groq token
        r"AIza[0-9A-Za-z\-_]{35}", # Google / Gemini API key
        r"(?i)(api[_-]?key|secret[_-]?key|password|passwd|token)[\s=:\"]+[\w\-\.]{8,}",
        r"sk-[a-zA-Z0-9]{32,}",    # OpenAI token
    ]

    ALLOWED_DOMAINS = [
        "api.groq.com",
        "generativelanguage.googleapis.com",
        "api.github.com",
        "supabase.co",
        "api.coingecko.com",
        "api.llama.fi",
        "duckduckgo.com",
        "pypi.org",
        "files.pythonhosted.org",
        "npmjs.com",
        "raw.githubusercontent.com",
        "localhost",
        "127.0.0.1",
    ]

    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path or os.getenv("LOGS_PATH", "./logs")
        Path(self.log_path).mkdir(parents=True, exist_ok=True)
        self.audit_file = Path(self.log_path) / "security.log"
        self._compiled_blocked = [re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS]
        self._compiled_secrets = [re.compile(p) for p in self.SECRET_PATTERNS]

    # ------------------------------------------------------------------
    # CAPA 1 — Path Validation
    # ------------------------------------------------------------------
    def validate_path(self, path: str, operation: str = "access") -> bool:
        """Verifica que la ruta no apunte a zonas protegidas del sistema."""
        try:
            abs_path = str(Path(path).resolve())
        except Exception:
            self._audit("PATH_BLOCKED", f"ruta invalida: {path[:100]}")
            return False

        for protected in self.PROTECTED_PATHS:
            if abs_path.lower().startswith(str(protected).lower()):
                self._audit("PATH_BLOCKED", f"{operation}: {abs_path}")
                return False
        self._audit("PATH_OK", f"{operation}: {abs_path}")
        return True

    # ------------------------------------------------------------------
    # CAPA 2 — Command Whitelist
    # ------------------------------------------------------------------
    def validate_command(self, command: str) -> bool:
        """Verifica whitelist y ausencia de patrones bloqueados."""
        for pattern in self._compiled_blocked:
            if pattern.search(command):
                self._audit("CMD_BLOCKED", f"patron peligroso: {command[:100]}")
                return False

        cmd_lower = command.strip().lower()
        for allowed in self.ALLOWED_COMMANDS:
            if cmd_lower.startswith(allowed.lower()):
                self._audit("CMD_OK", command[:100])
                return True

        self._audit("CMD_BLOCKED", f"no en whitelist: {command[:100]}")
        return False

    # ------------------------------------------------------------------
    # CAPA 3 — Network Audit
    # ------------------------------------------------------------------
    def validate_domain(self, url: str) -> bool:
        """Verifica que la URL pertenece a un dominio autorizado."""
        for domain in self.ALLOWED_DOMAINS:
            if domain in url:
                self._audit("NET_OK", url[:100])
                return True

        extra = os.getenv("ALLOWED_DOMAINS", "")
        for domain in extra.split(","):
            if domain.strip() and domain.strip() in url:
                self._audit("NET_OK", f"(custom) {url[:100]}")
                return True

        self._audit("NET_BLOCKED", url[:100])
        return False

    # ------------------------------------------------------------------
    # CAPA 4 — Secrets Detection
    # ------------------------------------------------------------------
    def scan_for_secrets(self, content: str) -> List[str]:
        """Escanea contenido buscando secretos. Retorna lista de hallazgos."""
        findings = []
        for pattern in self._compiled_secrets:
            if pattern.search(content):
                findings.append(f"Posible secreto detectado (patron: {pattern.pattern[:40]}...)")
                self._audit("SECRET_DETECTED", f"patron: {pattern.pattern[:40]}")
        return findings

    def sanitize_output(self, content: str) -> str:
        """Reemplaza secretos detectados con [REDACTED] antes de guardar/mostrar."""
        for pattern in self._compiled_secrets:
            content = pattern.sub("[REDACTED]", content)
        return content

    # ------------------------------------------------------------------
    # CAPA 5 — Audit Log
    # ------------------------------------------------------------------
    def _audit(self, event: str, detail: str) -> None:
        """Registra un evento de seguridad con timestamp UTC."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{event}] {detail}\n"
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass  # El log no debe interrumpir el flujo de negocio
        if "BLOCKED" in event or "DETECTED" in event:
            logger.warning(f"SECURITY {event}: {detail}")
        else:
            logger.debug(f"SECURITY {event}: {detail}")
