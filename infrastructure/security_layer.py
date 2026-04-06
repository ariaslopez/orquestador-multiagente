"""SecurityLayer — 5 capas de proteccion para operaciones del sistema."""
from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path.cwd())).resolve()

BLOCKED_PATHS = [
    '/etc', '/sys', '/proc', '/boot', '/root',
    'C:\\Windows', 'C:\\System32', 'C:\\Program Files',
    os.path.expanduser('~/.ssh'),
    os.path.expanduser('~/.aws'),
]

ALLOWED_COMMANDS = [
    'pip install', 'pip3 install',
    'npm install', 'yarn install',
    'cargo build', 'cargo run',
    'go mod tidy', 'go build',
    'python ', 'python3 ',
    'pytest', 'unittest',
]

ALLOWED_DOMAINS = [
    'api.groq.com',
    'generativelanguage.googleapis.com',
    'supabase.co',
    'api.github.com',
    'api.coingecko.com',
    'pypi.org', 'files.pythonhosted.org',
    'duckduckgo.com',
    'localhost', '127.0.0.1',
]

SECRET_PATTERNS = [
    r'(?i)(api[_-]?key|secret[_-]?key|password|passwd|token)[\s=:"]+[\w\-\.]{8,}',
    r'sk-[a-zA-Z0-9]{32,}',
    r'gsk_[a-zA-Z0-9]{40,}',
    r'ghp_[a-zA-Z0-9]{36}',
]


class SecurityLayer:
    @staticmethod
    def validate_path(path: str) -> tuple[bool, str]:
        """Capa 1: valida que el path no apunte a directorios del sistema."""
        resolved = Path(path).resolve()
        for blocked in BLOCKED_PATHS:
            if str(resolved).startswith(str(blocked)):
                return False, f"Path bloqueado: acceso a {blocked} denegado"
        return True, ""

    @staticmethod
    def validate_command(command: str) -> tuple[bool, str]:
        """Capa 2: valida que el comando este en la whitelist."""
        cmd_lower = command.strip().lower()
        for allowed in ALLOWED_COMMANDS:
            if cmd_lower.startswith(allowed.lower()):
                return True, ""
        return False, f"Comando no permitido: '{command}'. Solo se permiten: {', '.join(ALLOWED_COMMANDS)}"

    @staticmethod
    def validate_domain(url: str) -> tuple[bool, str]:
        """Capa 3: valida que la URL apunte a un dominio permitido."""
        for domain in ALLOWED_DOMAINS:
            if domain in url:
                return True, ""
        return False, f"Dominio no permitido en: {url}"

    @staticmethod
    def scan_secrets(content: str) -> list[str]:
        """Capa 4: detecta posibles secrets hardcodeados en el contenido."""
        findings = []
        for pattern in SECRET_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                findings.append(f"Posible secret detectado (patron: {pattern[:30]}...)")
        return findings

    @staticmethod
    def sanitize_output(content: str) -> str:
        """Capa 5: remueve secrets del output antes de guardarlo."""
        for pattern in SECRET_PATTERNS:
            content = re.sub(pattern, '[REDACTED]', content)
        return content
