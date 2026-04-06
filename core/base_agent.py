"""Contrato base para todos los agentes del sistema."""
from abc import ABC, abstractmethod
from typing import Any
from .context import AgentContext


class BaseAgent(ABC):
    """
    Clase base que deben heredar todos los agentes.
    
    Contrato:
        - Recibe un AgentContext con el estado actual
        - Ejecuta su tarea específica
        - Devuelve el AgentContext enriquecido con su resultado
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.enabled = True

    @abstractmethod
    def run(self, context: AgentContext) -> AgentContext:
        """
        Ejecuta la tarea del agente.
        
        Args:
            context: Estado compartido del pipeline
            
        Returns:
            context enriquecido con el resultado de este agente
        """
        pass

    def can_run(self, context: AgentContext) -> bool:
        """Verifica si el agente puede ejecutarse con el contexto actual."""
        return self.enabled

    def on_error(self, context: AgentContext, error: Exception) -> AgentContext:
        """Manejo de errores. Puede ser sobreescrito por subclases."""
        context.add_error(self.name, str(error))
        return context

    def __repr__(self):
        return f"<Agent:{self.name}>"
