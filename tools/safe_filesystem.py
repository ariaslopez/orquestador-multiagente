"""SafeFileSystem — Operaciones de filesystem con validacion de seguridad."""
from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import Optional, List
from infrastructure.security_layer import SecurityLayer
from infrastructure.audit_logger import AuditLogger

_audit = AuditLogger()


class SafeFileSystem:
    def __init__(self, base_dir: str = 'output'):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write(self, relative_path: str, content: str, actor: str = 'system') -> Path:
        """Escribe un archivo de forma segura."""
        full_path = (self.base_dir / relative_path).resolve()
        ok, reason = SecurityLayer.validate_path(str(full_path))
        if not ok:
            _audit.log_security_violation(actor, 'PATH_VIOLATION', reason)
            raise PermissionError(reason)
        secrets = SecurityLayer.scan_secrets(content)
        if secrets:
            for s in secrets:
                _audit.log_security_violation(actor, 'SECRET_IN_CONTENT', s)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        _audit.log_file_write(actor, str(full_path), len(content.encode('utf-8')))
        return full_path

    def read(self, relative_path: str) -> str:
        """Lee un archivo."""
        full_path = (self.base_dir / relative_path).resolve()
        ok, reason = SecurityLayer.validate_path(str(full_path))
        if not ok:
            raise PermissionError(reason)
        return full_path.read_text(encoding='utf-8')

    def list_dir(self, relative_path: str = '.') -> List[str]:
        """Lista archivos en un directorio."""
        target = (self.base_dir / relative_path).resolve()
        if not target.exists():
            return []
        return [str(p.relative_to(self.base_dir)) for p in target.rglob('*') if p.is_file()]

    def delete(self, relative_path: str, actor: str = 'system') -> None:
        """Elimina un archivo."""
        full_path = (self.base_dir / relative_path).resolve()
        ok, reason = SecurityLayer.validate_path(str(full_path))
        if not ok:
            raise PermissionError(reason)
        full_path.unlink(missing_ok=True)
        _audit.log('FILE_DELETE', actor, 'delete', str(full_path))
