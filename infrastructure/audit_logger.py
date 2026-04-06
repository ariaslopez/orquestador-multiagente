"""AuditLogger — Registro completo de todas las operaciones del sistema."""
from __future__ import annotations
import os
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(os.getenv('AUDIT_LOG_PATH', 'data/security.log'))
TRACE_LOG_PATH = Path(os.getenv('TRACE_LOG_PATH', 'data/traces.log'))


class AuditLogger:
    def __init__(self):
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        TRACE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

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

    def log_agent_trace(
        self,
        agent_name: str,
        pipeline: str,
        session_id: str,
        duration_ms: float,
        tokens: int,
        cost_usd: float,
        status: str = 'ok',
    ) -> None:
        """Registra métricas de tiempo, tokens y costo por agente individual."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'AGENT_TRACE',
            'agent': agent_name,
            'pipeline': pipeline,
            'session_id': session_id,
            'duration_ms': round(duration_ms, 2),
            'tokens': tokens,
            'cost_usd': round(cost_usd, 6),
            'status': status,
        }
        with open(TRACE_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

    def get_pipeline_stats(self, pipeline: str = None, limit: int = 100) -> dict:
        """Agrega métricas de trazas: tokens totales, costo, duración promedio por pipeline."""
        if not TRACE_LOG_PATH.exists():
            return {}

        lines = TRACE_LOG_PATH.read_text(encoding='utf-8').strip().split('\n')
        stats: dict = defaultdict(lambda: {'calls': 0, 'total_tokens': 0, 'total_cost_usd': 0.0, 'total_duration_ms': 0.0, 'errors': 0})

        for line in lines[-limit:]:
            try:
                entry = json.loads(line)
                if entry.get('event_type') != 'AGENT_TRACE':
                    continue
                pipe = entry.get('pipeline', 'unknown')
                if pipeline and pipe != pipeline:
                    continue
                s = stats[pipe]
                s['calls'] += 1
                s['total_tokens'] += entry.get('tokens', 0)
                s['total_cost_usd'] += entry.get('cost_usd', 0.0)
                s['total_duration_ms'] += entry.get('duration_ms', 0.0)
                if entry.get('status') != 'ok':
                    s['errors'] += 1
            except Exception:
                pass

        result = {}
        for pipe, s in stats.items():
            calls = s['calls'] or 1
            result[pipe] = {
                'calls': s['calls'],
                'total_tokens': s['total_tokens'],
                'total_cost_usd': round(s['total_cost_usd'], 6),
                'avg_duration_ms': round(s['total_duration_ms'] / calls, 1),
                'error_rate': round(s['errors'] / calls, 3),
            }
        return result

    def get_most_used_pipeline(self) -> str:
        """Retorna el pipeline con más llamadas registradas."""
        stats = self.get_pipeline_stats()
        if not stats:
            return 'unknown'
        return max(stats, key=lambda p: stats[p]['calls'])

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
