"""SecuritySandbox — 5 capas de protección para operaciones del sistema."""
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
    5 capas de seguridad:
    1. Path Validation — verifica rutas contra directorios peligrosos
    2. Command Whitelist — solo comandos permitidos
    3. Network Audit — verifica dominios permitidos
    4. Secrets Protection — detecta datos sensibles en outputs
    5. Audit Log — registra TODA operación de seguridad
    """

    PROTECTED_PATHS = [
        "C:/Windows", "C:/System32", "C:/Program Files",
        "/etc", "/sys", "/boot", "/root", "/bin", "/sbin", "/usr/bin",
    ]

    ALLOWED_COMMANDS = [
        "pip install", "pip uninstall",
        "npm install", "npm run",
        "python", "python3",
        "node", "npx",
        "cargo build", "cargo run",
        "go build", "go run",
        "pytest", "jest",
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
        r"[Aa][Pp][Ii][_]?[Kk][Ee][Yy]\s*=\s*[\'\"][^\'\"]{{10,}}",
        r"[Ss][Ee][Cc][Rr][Ee][Tt]\s*=\s*[\'\"][^\'\"]{{10,}}",
        r"[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]\s*=\s*[\'\"][^\'\"]{{8,}}",
        r"[Tt][Oo][Kk][Ee][Nn]\s*=\s*[\'\"][^\'\"]{{10,}}",
        r"ghp_[a-zA-Z0-9]{{36}}",  # GitHub token
        r"gsk_[a-zA-Z0-9]{{52}}",  # Groq token
        r"AIza[0-9A-Za-z\-_]{{35}}",  # Google API key
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
        "npmjs.com",
        "raw.githubusercontent.com",
    ]

    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path or os.getenv("LOGS_PATH", "./logs")
        Path(self.log_path).mkdir(parents=True, exist_ok=True)
        self.audit_file = Path(self.log_path) / "security.log"

    # ------------------------------------------------------------------
    # CAPA 1 — Path Validation
    # ------------------------------------------------------------------
    def validate_path(self, path: str, operation: str = "access") -> bool:
        """Verifica que la ruta no esté en zonas protegidas."""
        abs_path = str(Path(path).resolve())
        for protected in self.PROTECTED_PATHS:
            if abs_path.lower().startswith(protected.lower()):
                self._audit("PATH_BLOCKED", f"{operation}: {abs_path}")
                return False
        self._audit("PATH_OK", f"{operation}: {abs_path}")
        return True

    # ------------------------------------------------------------------
    # CAPA 2 — Command Whitelist
    # ------------------------------------------------------------------
    def validate_command(self, command: str) -> bool:
        """Verifica que el comando esté en la whitelist y no tenga patrones bloqueados."""
        # Verificar patrones bloqueados primero
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                self._audit("CMD_BLOCKED", f"Patrón peligroso: {command[:100]}")
                return False

        # Verificar que el comando empiece con algo permitido
        cmd_lower = command.strip().lower()
        for allowed in self.ALLOWED_COMMANDS:
            if cmd_lower.startswith(allowed.lower()):
                self._audit("CMD_OK", command[:100])
                return True

        self._audit("CMD_BLOCKED", f"No en whitelist: {command[:100]}")
        return False

    # ------------------------------------------------------------------
    # CAPA 3 — Network Audit
    # ------------------------------------------------------------------
    def validate_domain(self, url: str) -> bool:
        """Verifica que la URL pertenece a un dominio permitido."""
        for domain in self.ALLOWED_DOMAINS:
            if domain in url:
                self._audit("NET_OK", url[:100])
                return True

        # También permitir dominios adicionales del .env
        extra = os.getenv("ALLOWED_DOMAINS", "")
        for domain in extra.split(","):
            if domain.strip() and domain.strip() in url:
                self._audit("NET_OK", f"(custom) {url[:100]}")
                return True

        self._audit("NET_BLOCKED", url[:100])
        return False

    # ------------------------------------------------------------------
    # CAPA 4 — Secrets Protection
    # ------------------------------------------------------------------
    def scan_for_secrets(self, content: str) -> List[str]:
        """Escanea contenido en busca de secretos expuestos. Retorna lista de hallazgos."""
        findings = []
        for pattern in self.SECRET_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                findings.append(f"Posible secreto detectado (patrón: {pattern[:30]}...)")
                self._audit("SECRET_DETECTED", f"Patrón: {pattern[:30]}")
        return findings

    def sanitize_output(self, content: str) -> str:
        """Reemplaza secretos detectados con [REDACTED]."""
        for pattern in self.SECRET_PATTERNS:
            content = re.sub(pattern, "[REDACTED]", content)
        return content

    # ------------------------------------------------------------------
    # CAPA 5 — Audit Log
    # ------------------------------------------------------------------
    def _audit(self, event: str, detail: str) -> None:
        """Registra un evento de seguridad en el log."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{event}] {detail}\n"
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass  # No interrumpir el flujo por un error de log
        if "BLOCKED" in event or "DETECTED" in event:
            logger.warning(f"SECURITY {event}: {detail}")
        else:
            logger.debug(f"SECURITY {event}: {detail}")
