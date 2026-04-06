"""Orquestador central: coordina la ejecución de los agentes."""
import logging
from typing import List, Optional
from .base_agent import BaseAgent
from .context import AgentContext
from .pipeline import Pipeline

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    El Maestro del sistema. Recibe una tarea, selecciona el pipeline
    adecuado y coordina la ejecución secuencial o paralela de agentes.
    """

    def __init__(self):
        self.pipelines: dict[str, Pipeline] = {}
        self.default_pipeline: Optional[str] = None

    def register_pipeline(self, pipeline: Pipeline, default: bool = False):
        """Registra un pipeline de agentes."""
        self.pipelines[pipeline.name] = pipeline
        if default:
            self.default_pipeline = pipeline.name
        logger.info(f"Pipeline registrado: {pipeline.name} ({len(pipeline.agents)} agentes)")

    def run(self, query: str, pipeline_name: Optional[str] = None, **kwargs) -> AgentContext:
        """
        Ejecuta un pipeline completo para una consulta dada.
        
        Args:
            query: Pregunta o tarea del usuario
            pipeline_name: Nombre del pipeline a usar (usa default si no se indica)
            **kwargs: Parámetros adicionales para el contexto
        """
        name = pipeline_name or self.default_pipeline
        if not name or name not in self.pipelines:
            raise ValueError(f"Pipeline '{name}' no encontrado. Pipelines disponibles: {list(self.pipelines.keys())}")

        context = AgentContext(
            user_query=query,
            pipeline_name=name,
            **kwargs
        )

        logger.info(f"Iniciando pipeline '{name}' para query: '{query[:60]}...'")
        context = self.pipelines[name].execute(context)
        logger.info(f"Pipeline '{name}' finalizado. Agentes ejecutados: {context.agents_executed}")

        return context

    def list_pipelines(self) -> List[str]:
        return list(self.pipelines.keys())
