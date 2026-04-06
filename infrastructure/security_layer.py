"""SecurityLayer — DEPRECATED: shim de compatibilidad hacia SecuritySandbox.

Esta clase era codigo duplicado de SecuritySandbox con metodos estaticos
y sin audit log. Ha sido unificada en SecuritySandbox (la clase canonica).

Si algun modulo la importa, seguira funcionando via delegacion.
Para codigo nuevo: usar SecuritySandbox directamente.

  from infrastructure.security_sandbox import SecuritySandbox
  sandbox = SecuritySandbox()
"""
from __future__ import annotations
from infrastructure.security_sandbox import SecuritySandbox

_sandbox = SecuritySandbox()


class SecurityLayer:
    """Shim backward-compatible. Delega a SecuritySandbox."""

    @staticmethod
    def validate_path(path: str) -> tuple[bool, str]:
        ok = _sandbox.validate_path(path)
        return ok, "" if ok else f"Path bloqueado: {path}"

    @staticmethod
    def validate_command(command: str) -> tuple[bool, str]:
        ok = _sandbox.validate_command(command)
        return ok, "" if ok else f"Comando no permitido: {command}"

    @staticmethod
    def validate_domain(url: str) -> tuple[bool, str]:
        ok = _sandbox.validate_domain(url)
        return ok, "" if ok else f"Dominio no permitido: {url}"

    @staticmethod
    def scan_secrets(content: str) -> list[str]:
        return _sandbox.scan_for_secrets(content)

    @staticmethod
    def sanitize_output(content: str) -> str:
        return _sandbox.sanitize_output(content)
