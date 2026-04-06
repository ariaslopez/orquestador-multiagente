"""Estado compartido que fluye entre agentes en el pipeline."""
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class AgentContext:
    """
    Contenedor de estado que pasa entre agentes.
    Cada agente puede leer y enriquecer este contexto.
    """

    # Input del usuario
    user_query: str = ""
    user_files: list = field(default_factory=list)   # archivos adjuntos
    language: Optional[str] = None                   # lenguaje detectado (python, js, etc.)

    # Resultados de cada agente
    detected_language: Optional[str] = None
    relevant_docs: list = field(default_factory=list)
    code_analysis: Optional[dict] = None
    search_results: list = field(default_factory=list)
    final_response: Optional[str] = None

    # Metadatos del pipeline
    pipeline_name: str = ""
    agents_executed: list = field(default_factory=list)
    errors: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_error(self, agent_name: str, error_msg: str):
        """Registra un error de un agente."""
        self.errors[agent_name] = error_msg

    def mark_agent_done(self, agent_name: str):
        """Marca un agente como ejecutado."""
        self.agents_executed.append(agent_name)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def set_meta(self, key: str, value: Any):
        """Almacena metadata arbitraria en el contexto."""
        self.metadata[key] = value

    def get_meta(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)
