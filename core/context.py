"""AgentContext — Estado compartido entre agentes durante una sesión."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class AgentContext:
    """Estado compartido que fluye entre todos los agentes de un pipeline."""

    # Identificadores
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Input original del usuario
    user_input: str = ""
    task_type: str = ""          # dev | research | content | office | qa | pm | trading
    pipeline_name: str = ""
    environment: str = "local"   # local | server

    # Archivos adjuntos
    input_file: Optional[str] = None
    input_repo: Optional[str] = None

    # Estado del pipeline
    current_agent: str = ""
    completed_agents: List[str] = field(default_factory=list)
    failed_agents: List[str] = field(default_factory=list)
    retry_counts: Dict[str, int] = field(default_factory=dict)

    # Datos que los agentes producen y consumen
    data: Dict[str, Any] = field(default_factory=dict)

    # Output final
    final_output: Optional[str] = None
    output_path: Optional[str] = None
    output_files: List[str] = field(default_factory=list)

    # Métricas
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    apis_used: List[str] = field(default_factory=list)

    # Logs detallados por agente
    agent_logs: Dict[str, List[str]] = field(default_factory=dict)

    # Estado general
    status: str = "pending"      # pending | running | completed | failed | paused
    error: Optional[str] = None

    def log(self, agent_name: str, message: str) -> None:
        """Agrega un log entry para un agente específico."""
        if agent_name not in self.agent_logs:
            self.agent_logs[agent_name] = []
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        self.agent_logs[agent_name].append(f"[{timestamp}] {message}")

    def set_data(self, key: str, value: Any) -> None:
        """Guarda un dato en el contexto compartido."""
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """Recupera un dato del contexto compartido."""
        return self.data.get(key, default)

    def mark_agent_done(self, agent_name: str) -> None:
        self.completed_agents.append(agent_name)

    def mark_agent_failed(self, agent_name: str, error: str) -> None:
        self.failed_agents.append(agent_name)
        self.log(agent_name, f"ERROR: {error}")

    def increment_retry(self, agent_name: str) -> int:
        self.retry_counts[agent_name] = self.retry_counts.get(agent_name, 0) + 1
        return self.retry_counts[agent_name]

    def add_tokens(self, tokens: int, cost: float = 0.0, api: str = "") -> None:
        self.total_tokens += tokens
        self.estimated_cost_usd += cost
        if api and api not in self.apis_used:
            self.apis_used.append(api)

    def finish(self, status: str = "completed") -> None:
        self.finished_at = datetime.utcnow()
        self.status = status

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return (datetime.utcnow() - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el contexto para guardarlo en Supabase o SQLite."""
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "user_input": self.user_input,
            "task_type": self.task_type,
            "pipeline_name": self.pipeline_name,
            "environment": self.environment,
            "status": self.status,
            "final_output": self.final_output,
            "output_path": self.output_path,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "apis_used": self.apis_used,
            "duration_seconds": self.duration_seconds,
            "completed_agents": self.completed_agents,
            "failed_agents": self.failed_agents,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }
