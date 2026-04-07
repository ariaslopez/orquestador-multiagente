"""Maestro — Cerebro central del sistema CLAW Agent System.

Cadena de pensamiento activa:
  classify_task()            → scoring rápido por keywords
  _resolve_tie()             → detecta empates y escala al LLM
  classify_task_with_llm()   → LLM con chain-of-thought explícito (thinking)
  run()                      → orquesta memoria + pipeline + loop controller
"""
from __future__ import annotations
import os
import logging
from typing import Optional, Dict, List, Tuple
from .context import AgentContext
from .api_router import APIRouter
from .pipeline_router import PipelineRouter

logger = logging.getLogger(__name__)


class Maestro:
    """
    El Maestro es el orquestador central del sistema CLAW.

    Responsabilidades:
    1. Clasificar la tarea (keyword scoring → desempate LLM con CoT)
    2. Consultar memoria (¿existe algo similar ya resuelto?)
    3. Construir el pipeline de agentes correcto
    4. Ejecutar el pipeline vía PipelineRouter + LoopController (Fase 12)
    5. Guardar resultados en memoria
    6. Reportar al usuario
    """

    TASK_KEYWORDS: Dict[str, List[str]] = {
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
        "analytics": [
            "dashboard", "kpi", "metricas de negocio", "insights",
            "reporte semanal", "analytics", "cohort", "retention",
            "conversion rate", "funnel", "datos de negocio",
        ],
        "marketing": [
            "marketing", "campana", "publicidad", "ads", "copy",
            "landing page", "email marketing", "cac", "ltv",
            "growth", "adquisicion", "posicionamiento", "marca",
        ],
        "product": [
            "producto", "feature", "roadmap de producto", "priorizacion",
            "user story", "feedback de usuarios", "jtbd", "mvp",
            "product market fit", "onboarding", "retencion",
        ],
        "security_audit": [
            "owasp", "pentest", "auditoria de seguridad", "vulnerabilidades",
            "gdpr", "compliance", "threat model", "stride",
            "inyeccion sql", "xss", "csrf", "autenticacion",
        ],
        "design": [
            "disena", "ui", "ux", "interfaz", "wireframe", "prototipo",
            "design system", "componentes", "figma", "tipografia",
            "paleta de colores", "accesibilidad", "wcag", "branding",
        ],
    }

    # Score mínimo para confiar en keyword matching sin consultar el LLM
    _CONFIDENT_SCORE_THRESHOLD = 2

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

    # ------------------------------------------------------------------
    # Clasificación con cadena de pensamiento
    # ------------------------------------------------------------------

    def classify_task(self, user_input: str) -> Tuple[str, int, bool]:
        """
        Clasifica la tarea por keyword scoring.

        Retorna: (task_type, best_score, needs_llm)
          - needs_llm=True si hay empate o score < threshold
        """
        lower = user_input.lower()
        scores: Dict[str, int] = {task: 0 for task in self.TASK_KEYWORDS}

        for task, keywords in self.TASK_KEYWORDS.items():
            for kw in keywords:
                if kw in lower:
                    scores[task] += 1

        sorted_tasks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_task, best_score = sorted_tasks[0]
        second_task, second_score = sorted_tasks[1] if len(sorted_tasks) > 1 else ("", -1)

        # Empate: dos pipelines con el mismo score máximo
        tie = best_score > 0 and best_score == second_score
        # Score bajo: no hay evidencia suficiente para confiar sin LLM
        low_confidence = best_score < self._CONFIDENT_SCORE_THRESHOLD

        needs_llm = tie or low_confidence

        if tie:
            logger.info(
                f"Clasificacion: EMPATE entre '{best_task}' y '{second_task}' "
                f"(score={best_score}) → escalando a LLM"
            )
        elif low_confidence:
            logger.info(
                f"Clasificacion: score bajo ({best_score}) en '{best_task}' "
                f"→ verificando con LLM"
            )
        else:
            logger.info(
                f"Clasificacion: '{best_task}' (score={best_score}, confianza=alta)"
            )

        return best_task, best_score, needs_llm

    async def classify_task_with_llm(
        self, user_input: str, candidates: Optional[List[str]] = None
    ) -> str:
        """
        Clasificación con cadena de pensamiento (chain-of-thought).

        El LLM razona en voz alta (<thinking>) antes de responder,
        lo que reduce errores en casos ambiguos. Compatible con:
          - qwen2.5-coder via /think tag (Ollama local)
          - llama-3.3-70b vía Groq (razonamiento implícito)
          - gemini-2.0-flash (razonamiento interno)
        """
        valid_types = {
            "dev", "research", "content", "office", "qa", "pm", "trading",
            "analytics", "marketing", "product", "security_audit", "design",
        }

        # Si hay candidatos específicos por empate, mencionarlos en el prompt
        candidate_hint = ""
        if candidates and len(candidates) >= 2:
            candidate_hint = (
                f"\nHay ambigüedad entre: {', '.join(candidates)}. "
                "Decide cuál encaja MEJOR con la tarea concreta."
            )

        # Prompt con chain-of-thought explícito
        # El tag /think activa razonamiento interno en modelos qwen locales
        prompt = f"""/think
Análisis de clasificación de tarea:

Tarea del usuario: "{user_input}"
{candidate_hint}

Pipelines disponibles:
- dev: crear software, bots, APIs, scripts, código nuevo
- research: análisis, tesis, investigación de activos crypto/mercados
- content: generar contenido para redes sociales, blogs, newsletters
- office: analizar archivos Excel, Word, PDF, PowerPoint
- qa: auditar, revisar, validar código existente, buscar bugs
- pm: planificar proyectos, crear backlog, sprints, roadmaps de gestión
- trading: analizar bots de trading, logs, backtests, métricas de performance
- analytics: KPIs, dashboards, insights de negocio, reportes de datos
- marketing: campañas, copy, growth, CAC/LTV, posicionamiento de marca
- product: features, roadmap de producto, feedback de usuarios, priorización
- security_audit: OWASP, threat modeling, compliance GDPR, pentest
- design: UI/UX, design system, branding, accesibilidad WCAG

Piensa paso a paso:
1. ¿Cuál es el VERBO principal de la tarea? (crear, analizar, auditar...)
2. ¿Cuál es el OBJETO? (código, archivo, mercado, contenido...)
3. ¿Cuál pipeline coincide exactamente?

Responde SOLO con la categoría, sin explicación ni puntuación."""

        result, _ = await self.api_router.complete(
            messages=[{"role": "user", "content": prompt}],
            task_type="classification",
            temperature=0.1,
            max_tokens=20,
        )

        # Limpiar respuesta: quitar bloques <thinking>...</thinking> si el modelo los expone
        import re
        clean = re.sub(r"<thinking>.*?</thinking>", "", result, flags=re.DOTALL)
        task_type = clean.strip().lower().split()[0] if clean.strip() else "dev"
        task_type = task_type.strip(".,;:")

        if task_type not in valid_types:
            logger.warning(
                f"LLM clasificó como '{task_type}' (inválido) → usando 'dev' por defecto"
            )
            return "dev"

        logger.info(f"Clasificacion LLM (CoT): '{task_type}'")
        return task_type

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------

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
        Punto de entrada principal.

        Flujo:
          1. Crear contexto de sesión
          2. Clasificar tarea (keyword → CoT LLM si hay ambigüedad)
          3. Consultar memoria episódica
          4. Ejecutar pipeline
          5. Persistir sesión
        """
        ctx = AgentContext(
            user_input=user_input,
            environment=self.environment,
            input_file=input_file,
            input_repo=input_repo,
            output_path=output_path or os.getenv("OUTPUT_PATH", "./output"),
        )

        # --- Clasificación inteligente ---
        if task_type:
            ctx.task_type = task_type
            logger.info(f"Maestro.run() | task_type forzado: {task_type}")
        else:
            best_task, best_score, needs_llm = self.classify_task(user_input)

            if needs_llm:
                # Determinar candidatos para el hint de desempate
                sorted_scores = sorted(
                    {t: 0 for t in self.TASK_KEYWORDS}.items(),
                    key=lambda x: x[1], reverse=True
                )
                # Recalcular para tener los scores reales
                real_scores: Dict[str, int] = {t: 0 for t in self.TASK_KEYWORDS}
                lower = user_input.lower()
                for t, kws in self.TASK_KEYWORDS.items():
                    for kw in kws:
                        if kw in lower:
                            real_scores[t] += 1
                top = sorted(real_scores.items(), key=lambda x: x[1], reverse=True)
                candidates = [t for t, s in top[:3] if s == top[0][1]] if top[0][1] > 0 else []
                ctx.task_type = await self.classify_task_with_llm(user_input, candidates)
            else:
                ctx.task_type = best_task

        ctx.pipeline_name = ctx.task_type
        ctx.status = "running"
        logger.info(
            f"Maestro.run() | task_type={ctx.task_type} | session={ctx.session_id[:8]}"
        )
        ctx.log("maestro", f"Tarea clasificada como: {ctx.task_type}")

        # --- Memoria episódica ---
        if self.memory:
            similar = await self.memory.find_similar(user_input, ctx.task_type)
            if similar:
                ctx.set_data("memory_context", similar)
                ctx.log(
                    "maestro",
                    f"Memoria: encontrado contexto previo ({len(similar)} entradas)",
                )

        # --- Ejecución del pipeline ---
        try:
            ctx = await self._execute_pipeline(ctx)
            ctx.finish("completed")
            ctx.log("maestro", f"Pipeline completado en {ctx.duration_seconds:.1f}s")
        except Exception as e:
            ctx.error = str(e)
            ctx.finish("failed")
            ctx.log("maestro", f"Pipeline falló: {e}")
            logger.error(f"Maestro: pipeline falló: {e}", exc_info=True)

        # --- Persistencia ---
        if self.memory:
            await self.memory.save_session(ctx)

        return ctx

    # ------------------------------------------------------------------
    # Ejecución de pipeline
    # ------------------------------------------------------------------

    async def _execute_pipeline(self, ctx: AgentContext) -> AgentContext:
        """Construye el pipeline correcto y lo ejecuta."""
        pipeline_map = {
            "dev":            self._build_dev_pipeline,
            "research":       self._build_research_pipeline,
            "content":        self._build_content_pipeline,
            "office":         self._build_office_pipeline,
            "qa":             self._build_qa_pipeline,
            "pm":             self._build_pm_pipeline,
            "trading":        self._build_trading_pipeline,
            "analytics":      self._build_analytics_pipeline,
            "marketing":      self._build_marketing_pipeline,
            "product":        self._build_product_pipeline,
            "security_audit": self._build_security_audit_pipeline,
            "design":         self._build_design_pipeline,
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
        return await self.pipeline_router.run_sequential(sequential_agents, ctx)

    # ------------------------------------------------------------------
    # BUILDERS
    # ------------------------------------------------------------------

    def _build_dev_pipeline(self):
        from agents.dev.planner_agent import PlannerAgent
        from agents.dev.coder_agent import CoderAgent
        from agents.dev.reviewer_agent import ReviewerAgent
        from agents.dev.security_agent import SecurityAgent
        from agents.dev.executor_agent import ExecutorAgent
        from agents.dev.git_agent import GitAgent
        return [
            PlannerAgent(), CoderAgent(), ReviewerAgent(),
            SecurityAgent(), ExecutorAgent(), GitAgent(),
        ], [], "sequential"

    def _build_research_pipeline(self):
        from agents.research.webscout_agent import WebScoutAgent
        from agents.research.data_agent import DataAgent
        from agents.research.analyst_agent import AnalystAgent
        from agents.research.thesis_agent import ThesisAgent
        return [AnalystAgent(), ThesisAgent()], [WebScoutAgent(), DataAgent()], "parallel_then_sequential"

    def _build_content_pipeline(self):
        from agents.content.topic_agent import TopicAgent
        from agents.content.writer_agent import WriterAgent
        from agents.content.editor_agent import EditorAgent
        from agents.content.brand_agent import BrandAgent
        from agents.content.scheduler_agent import SchedulerAgent
        return [TopicAgent(), WriterAgent(), EditorAgent(), BrandAgent(), SchedulerAgent()], [], "sequential"

    def _build_office_pipeline(self):
        from agents.office.file_reader import FileReaderAgent
        from agents.office.data_analyzer import DataAnalyzerAgent
        from agents.office.report_writer import ReportWriterAgent
        return [FileReaderAgent(), DataAnalyzerAgent(), ReportWriterAgent()], [], "sequential"

    def _build_qa_pipeline(self):
        from agents.qa.static_analyzer import StaticAnalyzerAgent
        from agents.qa.bug_hunter import BugHunterAgent
        from agents.qa.security_reviewer import SecurityReviewerAgent
        from agents.qa.performance_profiler import PerformanceProfilerAgent
        from agents.qa.test_generator import TestGeneratorAgent
        return [
            StaticAnalyzerAgent(), BugHunterAgent(), SecurityReviewerAgent(),
            PerformanceProfilerAgent(), TestGeneratorAgent(),
        ], [], "sequential"

    def _build_pm_pipeline(self):
        from agents.pm.requirements_parser import RequirementsParserAgent
        from agents.pm.backlog_builder import BacklogBuilderAgent
        from agents.pm.sprint_planner import SprintPlannerAgent
        from agents.pm.roadmap_generator import RoadmapGeneratorAgent
        return [
            RequirementsParserAgent(), BacklogBuilderAgent(),
            SprintPlannerAgent(), RoadmapGeneratorAgent(),
        ], [], "sequential"

    def _build_trading_pipeline(self):
        from agents.trading.backtest_reader import BacktestReaderAgent
        from agents.trading.metrics_calculator import MetricsCalculatorAgent
        from agents.trading.risk_analyzer import RiskAnalyzerAgent
        from agents.trading.strategy_advisor import StrategyAdvisorAgent
        return [
            BacktestReaderAgent(), MetricsCalculatorAgent(),
            RiskAnalyzerAgent(), StrategyAdvisorAgent(),
        ], [], "sequential"

    def _build_analytics_pipeline(self):
        from agents.analytics.data_collector import DataCollectorAgent
        from agents.analytics.insight_generator import InsightGeneratorAgent
        from agents.analytics.report_distributor import ReportDistributorAgent
        return [DataCollectorAgent(), InsightGeneratorAgent(), ReportDistributorAgent()], [], "sequential"

    def _build_marketing_pipeline(self):
        from agents.marketing.strategy_agent import MarketingStrategyAgent
        from agents.marketing.copy_agent import CopyAgent
        from agents.marketing.growth_agent import GrowthAgent
        from agents.marketing.analytics_agent import MarketingAnalyticsAgent
        return [MarketingStrategyAgent(), CopyAgent(), GrowthAgent(), MarketingAnalyticsAgent()], [], "sequential"

    def _build_product_pipeline(self):
        from agents.product.market_researcher import MarketResearcherAgent
        from agents.product.feedback_synthesizer import FeedbackSynthesizerAgent
        from agents.product.feature_prioritizer import FeaturePrioritizerAgent
        from agents.product.nudge_designer import NudgeDesignerAgent
        return [
            MarketResearcherAgent(), FeedbackSynthesizerAgent(),
            FeaturePrioritizerAgent(), NudgeDesignerAgent(),
        ], [], "sequential"

    def _build_security_audit_pipeline(self):
        from agents.security.threat_modeler import ThreatModelerAgent
        from agents.security.code_reviewer import SecurityCodeReviewerAgent
        from agents.security.compliance_checker import ComplianceCheckerAgent
        return [ThreatModelerAgent(), SecurityCodeReviewerAgent(), ComplianceCheckerAgent()], [], "sequential"

    def _build_design_pipeline(self):
        from agents.design.ui_agent import UIAgent
        from agents.design.ux_agent import UXAgent
        from agents.design.brand_agent import DesignBrandAgent
        from agents.design.a11y_agent import A11yAgent
        from agents.design.prompt_engineer import PromptEngineerAgent
        return [UIAgent(), UXAgent(), DesignBrandAgent(), A11yAgent(), PromptEngineerAgent()], [], "sequential"
