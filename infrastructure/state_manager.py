"""StateManager — Checkpoints y recuperación ante interrupciones."""
from __future__ import annotations
import json
import logging
from typing import Optional, Dict, Any
from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class StateManager:
    """
    Gestiona checkpoints del pipeline para recuperación ante interrupciones.
    Si el sistema se detiene a mitad de una tarea, puede reanudar desde
    el último checkpoint guardado.
    """

    def __init__(self, memory: MemoryManager):
        self.memory = memory

    def save_checkpoint(self, session_id: str, agent_name: str, ctx_data: Dict[str, Any]) -> None:
        """Guarda el estado actual del pipeline."""
        self.memory.save_checkpoint(session_id, agent_name, ctx_data)
        logger.debug(f"Checkpoint guardado: session={session_id[:8]}, agent={agent_name}")

    def load_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Carga el último checkpoint disponible para una sesión."""
        checkpoint = self.memory.get_last_checkpoint(session_id)
        if checkpoint:
            logger.info(f"Checkpoint cargado: session={session_id[:8]}, agent={checkpoint.get('agent_name')}")
        return checkpoint

    def has_checkpoint(self, session_id: str) -> bool:
        return self.memory.get_last_checkpoint(session_id) is not None

    def clear_checkpoint(self, session_id: str) -> None:
        """Limpia checkpoints de una sesión completada."""
        conn = self.memory._get_conn()
        conn.execute("DELETE FROM checkpoints WHERE session_id = ?", (session_id,))
        conn.commit()
        logger.debug(f"Checkpoints limpiados para sesión {session_id[:8]}")
