"""Maestro — Cerebro central del sistema CLAW Agent System."""
from __future__ import annotations
import os
import logging
from typing import Optional, Dict, Any
from .context import AgentContext
from .api_router import APIRouter
from .pipeline_router import PipelineRouter

logger = logging.getLogger(__name__)


class Maestro:
    """
    El Maestro es el orquestador central del sistema CLAW.

    Responsabilidades:
    1. Clasificar la tarea del usuario (que tipo de pipeline usar)
    2. Consultar la memoria (ya existe algo similar?)
    3. Construir el pipeline de agentes correcto
    4. Ejecutar el pipeline via PipelineRouter
    5. Guardar resultados en memoria
    6. Reportar al usuario
    """

    # Keywords para clasificacion de tareas
    TASK_KEYWORDS = {
        "dev": [
            "crea", "construye", "desarrolla", "implementa", "programa",
            "bot", "api", "script", "sistema", "app", "aplicacion",
            "create", "build", "develop", "implement",
        ],
        "research": [
            "investiga", "analiza", "tesis", "research", "analisis",
            "comparativa", "estudio", "evalua", "tendencia", "mercado",
            "bitcoin", "ethereum", "crypto", "token", "defi", "nft",
        ],
        "content": [
            "tweet", "hilo", "post", "contenido", "redacta", "escribe",
            "newsletter", "blog", "thread", "content", "write",
        ],
        "office": [
            ".xlsx", ".csv", ".docx", ".pdf", ".pptx",
            "excel", "word", "powerpoint", "spreadsheet",
        ],
        "qa": [
            "audita", "revisa", "valida", "qa", "test", "bug",
            "vulnerabilidad", "seguridad", "calidad", "review",
        ],
        "pm": [
            "planifica", "backlog", "sprint", "tareas", "roadmap",
            "epicas", "estimacion", "plan", "project",
        ],
        "trading": [
            "bot de trading", "log", "backtest", "estrategia",
            "performance", "win rate", "drawdown", "sharpe",
            "senal", "trading",
        ],
    }

    def __init__(
        self,
        memory_manager=None,
        environment: Optional[str] = None,
    ):
        self.environment = environment or os.getenv("CLAW_ENV", "local")
        self.api_router = APIRouter()
        self.pipeline_router = PipelineRouter()
        self.memory = memory_manager
        logger.info(f"Maestro iniciado | Ambiente: {self.environment}")

    def classify_task(self, user_input: str) -> str:
        """
        Clasifica la tarea del usuario y retorna el tipo de pipeline.
        Usa keyword matching primero; si hay ambiguedad, consulta el LLM.
        """
        lower = user_input.lower()
        scores: Dict[str, int] = {task: 0 for task in self.TASK_KEYWORDS}

        for task, keywords in self.TASK_KEYWORDS.items():
            for kw in keywords:
                if kw in lower:
                    scores[task] += 1

        best_task = max(scores, key=lambda t: scores[t])
        best_score = scores[best_task]

        if best_score == 0:
            logger.info("Clasificacion: sin keywords claras, usando 'dev' por defecto")
            return "dev"

        logger.info(f"Clasificacion: '{best_task}' (score={best_score})")
        return best_task

    async def classify_task_with_llm(self, user_input: str) -> str:
        """
        Version mejorada: usa el LLM para clasificar con mejor precision.
        Usala cuando el keyword matching sea ambiguo.
        """
        prompt = f"""Clasifica esta tarea en UNA de estas categorias:
- dev: crear software, bots, APIs, scripts
- research: analisis, tesis, investigacion de activos crypto
- content: generar contenido para redes sociales, blogs
- office: analizar archivos Excel, Word, PDF, PowerPoint
- qa: auditar, revisar, validar codigo
- pm: planificar proyectos, crear backlog
- trading: analizar bots de trading, logs, backtests

Tarea: "{user_input}"

Responde SOLO con la categoria, sin explicacion."""

        # complete() retorna (text, tokens) — solo usamos el texto aqui
        result, _ = await self.api_router.complete(
            messages=[{"role": "user", "content": prompt}],
            task_type="classification",
            temperature=0.1,
            max_tokens=10,
        )
        task_type = result.strip().lower()
        valid = {"dev", "research", "content", "office", "qa", "pm", "trading"}
        return task_type if task_type in valid else "dev"

    async def run(
        self,
        user_input: str,
        task_type: Optional[str] = None,
        input_file: Optional[str] = None,
        input_repo: Optional[str] = None,
        output_path: Optional[str] = None,
        auto_mode: bool = False,
    ) -> AgentContext:
        """
        Punto de entrada principal. Recibe el input del usuario y ejecuta el pipeline.
        """
        # Crear contexto
        ctx = AgentContext(
            user_input=user_input,
            environment=self.environment,
            input_file=input_file,
            input_repo=input_repo,
            output_path=output_path or os.getenv("OUTPUT_PATH", "./output"),
        )

        # Clasificar tarea
        if task_type:
            ctx.task_type = task_type
        else:
            ctx.task_type = self.classify_task(user_input)
            # Si la clasificacion es ambigua, verificar con LLM
            if ctx.task_type == "dev" and not any(
                kw in user_input.lower() for kw in self.TASK_KEYWORDS["dev"]
            ):
                ctx.task_type = await self.classify_task_with_llm(user_input)

        ctx.pipeline_name = ctx.task_type
        ctx.status = "running"

        logger.info(f"Maestro.run() | task_type={ctx.task_type} | session={ctx.session_id[:8]}")
        ctx.log("maestro", f"Tarea clasificada como: {ctx.task_type}")

        # Consultar memoria — existe trabajo previo similar?
        if self.memory:
            similar = await self.memory.find_similar(user_input, ctx.task_type)
            if similar:
                ctx.set_data("memory_context", similar)
                ctx.log("maestro", f"Memoria: encontrado contexto previo ({len(similar)} entradas)")

        # Construir y ejecutar pipeline
        try:
            ctx = await self._execute_pipeline(ctx)
            ctx.finish("completed")
            ctx.log("maestro", f"Pipeline completado en {ctx.duration_seconds:.1f}s")
        except Exception as e:
            ctx.error = str(e)
            ctx.finish("failed")
            ctx.log("maestro", f"Pipeline fallo: {e}")
            logger.error(f"Maestro: pipeline fallo: {e}")

        # Guardar en memoria
        if self.memory:
            await self.memory.save_session(ctx)

        return ctx

    async def _execute_pipeline(self, ctx: AgentContext) -> AgentContext:
        """Construye el pipeline correcto y lo ejecuta."""
        pipeline_map = {
            "dev": self._build_dev_pipeline,
            "research": self._build_research_pipeline,
            "content": self._build_content_pipeline,
            "office": self._build_office_pipeline,
            "qa": self._build_qa_pipeline,
            "pm": self._build_pm_pipeline,
            "trading": self._build_trading_pipeline,
        }

        builder = pipeline_map.get(ctx.task_type)
        if not builder:
            raise ValueError(f"Pipeline desconocido: {ctx.task_type}")

        sequential_agents, parallel_agents, mode = builder()

        if mode == "parallel_then_sequential":
            return await self.pipeline_router.run_parallel_then_sequential(
                parallel_agents=parallel_agents,
                sequential_agents=sequential_agents,
                ctx=ctx,
            )
        else:
            return await self.pipeline_router.run_sequential(sequential_agents, ctx)

    # ------------------------------------------------------------------
    # BUILDERS — Cada pipeline define sus agentes
    # Se importan lazy para evitar dependencias circulares
    # ------------------------------------------------------------------

    def _build_dev_pipeline(self):
        from agents.dev.planner_agent import PlannerAgent
        from agents.dev.coder_agent import CoderAgent
        from agents.dev.reviewer_agent import ReviewerAgent
        from agents.dev.security_agent import SecurityAgent
        from agents.dev.executor_agent import ExecutorAgent
        from agents.dev.git_agent import GitAgent

        agents = [
            PlannerAgent(),
            CoderAgent(),
            ReviewerAgent(),
            SecurityAgent(),
            ExecutorAgent(),
            GitAgent(),
        ]
        return agents, [], "sequential"

    def _build_research_pipeline(self):
        from agents.research.webscout_agent import WebScoutAgent
        from agents.research.data_agent import DataAgent
        from agents.research.analyst_agent import AnalystAgent
        from agents.research.thesis_agent import ThesisAgent

        parallel = [WebScoutAgent(), DataAgent()]
        sequential = [AnalystAgent(), ThesisAgent()]
        return sequential, parallel, "parallel_then_sequential"

    def _build_content_pipeline(self):
        from agents.content.topic_agent import TopicAgent
        from agents.content.writer_agent import WriterAgent
        from agents.content.editor_agent import EditorAgent
        from agents.content.brand_agent import BrandAgent
        from agents.content.scheduler_agent import SchedulerAgent

        agents = [
            TopicAgent(),
            WriterAgent(),
            EditorAgent(),
            BrandAgent(),
            SchedulerAgent(),
        ]
        return agents, [], "sequential"

    def _build_office_pipeline(self):
        from agents.office.file_reader import FileReaderAgent
        from agents.office.data_analyzer import DataAnalyzerAgent
        from agents.office.report_writer import ReportWriterAgent

        agents = [
            FileReaderAgent(),
            DataAnalyzerAgent(),
            ReportWriterAgent(),
        ]
        return agents, [], "sequential"

    def _build_qa_pipeline(self):
        from agents.qa.static_analyzer import StaticAnalyzerAgent
        from agents.qa.bug_hunter import BugHunterAgent
        from agents.qa.security_reviewer import SecurityReviewerAgent
        from agents.qa.performance_profiler import PerformanceProfilerAgent
        from agents.qa.test_generator import TestGeneratorAgent

        agents = [
            StaticAnalyzerAgent(),
            BugHunterAgent(),
            SecurityReviewerAgent(),
            PerformanceProfilerAgent(),
            TestGeneratorAgent(),
        ]
        return agents, [], "sequential"

    def _build_pm_pipeline(self):
        from agents.pm.requirements_parser import RequirementsParserAgent
        from agents.pm.backlog_builder import BacklogBuilderAgent
        from agents.pm.sprint_planner import SprintPlannerAgent
        from agents.pm.roadmap_generator import RoadmapGeneratorAgent

        agents = [
            RequirementsParserAgent(),
            BacklogBuilderAgent(),
            SprintPlannerAgent(),
            RoadmapGeneratorAgent(),
        ]
        return agents, [], "sequential"

    def _build_trading_pipeline(self):
        from agents.trading.backtest_reader import BacktestReaderAgent
        from agents.trading.metrics_calculator import MetricsCalculatorAgent
        from agents.trading.risk_analyzer import RiskAnalyzerAgent
        from agents.trading.strategy_advisor import StrategyAdvisorAgent

        agents = [
            BacktestReaderAgent(),
            MetricsCalculatorAgent(),
            RiskAnalyzerAgent(),
            StrategyAdvisorAgent(),
        ]
        return agents, [], "sequential"
