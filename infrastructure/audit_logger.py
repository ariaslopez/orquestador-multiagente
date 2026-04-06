"""AuditLogger — Registro completo de todas las operaciones del sistema."""
from __future__ import annotations
import os
import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(os.getenv('AUDIT_LOG_PATH', 'data/security.log'))


class AuditLogger:
    def __init__(self):
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: str, actor: str, action: str, target: str = '', result: str = 'ok', metadata: dict = None) -> None:
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'actor': actor,
            'action': action,
            'target': target,
            'result': result,
            'metadata': metadata or {},
        }
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

    def log_file_write(self, agent: str, path: str, size_bytes: int) -> None:
        self.log('FILE_WRITE', agent, 'write', path, 'ok', {'size_bytes': size_bytes})

    def log_command(self, agent: str, command: str, allowed: bool) -> None:
        result = 'ok' if allowed else 'BLOCKED'
        self.log('COMMAND_EXEC', agent, command, '', result)

    def log_api_call(self, agent: str, url: str, model: str = '', tokens: int = 0) -> None:
        self.log('API_CALL', agent, 'llm_request', url, 'ok', {'model': model, 'tokens': tokens})

    def log_security_violation(self, agent: str, violation: str, detail: str = '') -> None:
        self.log('SECURITY_VIOLATION', agent, violation, '', 'BLOCKED', {'detail': detail})

    def get_recent_logs(self, limit: int = 50) -> list[dict]:
        if not LOG_PATH.exists():
            return []
        lines = LOG_PATH.read_text(encoding='utf-8').strip().split('\n')
        entries = []
        for line in lines[-limit:]:
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
        return entries
