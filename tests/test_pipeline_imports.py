"""Regression test: every agent declared in config.yaml must be importable.

Actua como guardia contra config/code drift:
si un pipeline declara un agente que no existe como clase Python,
el test falla inmediatamente — antes de cualquier error en produccion.

Run: pytest tests/test_pipeline_imports.py -v
"""
import sys
import importlib
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mapping: config agent names -> (module_path, class_name)
AGENT_REGISTRY = {
    # DEV
    "planner":  ("agents.dev.planner_agent",  "PlannerAgent"),
    "coder":    ("agents.dev.coder_agent",    "CoderAgent"),
    "reviewer": ("agents.dev.reviewer_agent", "ReviewerAgent"),
    "security": ("agents.dev.security_agent", "SecurityAgent"),
    "executor": ("agents.dev.executor_agent", "ExecutorAgent"),
    "git":      ("agents.dev.git_agent",      "GitAgent"),
    # RESEARCH
    "web_scout": ("agents.research.webscout_agent", "WebScoutAgent"),
    "data":      ("agents.research.data_agent",     "DataAgent"),
    "analyst":   ("agents.research.analyst_agent",  "AnalystAgent"),
    "thesis":    ("agents.research.thesis_agent",   "ThesisAgent"),
    # CONTENT
    "topic":     ("agents.content.topic_agent",     "TopicAgent"),
    "writer":    ("agents.content.writer_agent",    "WriterAgent"),
    "editor":    ("agents.content.editor_agent",    "EditorAgent"),
    "brand":     ("agents.content.brand_agent",     "BrandAgent"),
    "scheduler": ("agents.content.scheduler_agent", "SchedulerAgent"),
    # OFFICE
    "file_reader":   ("agents.office.file_reader",   "FileReaderAgent"),
    "data_analyzer": ("agents.office.data_analyzer", "DataAnalyzerAgent"),
    "report_writer": ("agents.office.report_writer", "ReportWriterAgent"),
    # QA
    "static_analyzer":    ("agents.qa.static_analyzer",    "StaticAnalyzerAgent"),
    "bug_hunter":         ("agents.qa.bug_hunter",         "BugHunterAgent"),
    "security_reviewer":  ("agents.qa.security_reviewer",  "SecurityReviewerAgent"),
    "performance_profiler": ("agents.qa.performance_profiler", "PerformanceProfilerAgent"),
    "test_generator":     ("agents.qa.test_generator",     "TestGeneratorAgent"),
    # PM
    "requirements_parser": ("agents.pm.requirements_parser", "RequirementsParserAgent"),
    "backlog_builder":     ("agents.pm.backlog_builder",     "BacklogBuilderAgent"),
    "sprint_planner":      ("agents.pm.sprint_planner",      "SprintPlannerAgent"),
    "roadmap_generator":   ("agents.pm.roadmap_generator",   "RoadmapGeneratorAgent"),
    # TRADING
    "backtest_reader":    ("agents.trading.backtest_reader",    "BacktestReaderAgent"),
    "metrics_calculator": ("agents.trading.metrics_calculator", "MetricsCalculatorAgent"),
    "risk_analyzer":      ("agents.trading.risk_analyzer",      "RiskAnalyzerAgent"),
    "strategy_advisor":   ("agents.trading.strategy_advisor",   "StrategyAdvisorAgent"),
    # ANALYTICS
    "data_collector":     ("agents.analytics.data_collector",   "DataCollectorAgent"),
    "insight_generator":  ("agents.analytics.insight_generator", "InsightGeneratorAgent"),
    "report_distributor": ("agents.analytics.report_distributor", "ReportDistributorAgent"),
    # MARKETING
    "strategy_agent":  ("agents.marketing.strategy_agent",  "MarketingStrategyAgent"),
    "copy_agent":      ("agents.marketing.copy_agent",      "CopyAgent"),
    "growth_agent":    ("agents.marketing.growth_agent",    "GrowthAgent"),
    "analytics_agent": ("agents.marketing.analytics_agent", "MarketingAnalyticsAgent"),
    # PRODUCT
    "market_researcher":   ("agents.product.market_researcher",   "MarketResearcherAgent"),
    "feedback_synthesizer":("agents.product.feedback_synthesizer","FeedbackSynthesizerAgent"),
    "feature_prioritizer": ("agents.product.feature_prioritizer", "FeaturePrioritizerAgent"),
    "nudge_designer":      ("agents.product.nudge_designer",      "NudgeDesignerAgent"),
    # SECURITY_AUDIT
    "threat_modeler":    ("agents.security.threat_modeler",    "ThreatModelerAgent"),
    "code_reviewer":     ("agents.security.code_reviewer",     "SecurityCodeReviewerAgent"),
    "compliance_checker":("agents.security.compliance_checker", "ComplianceCheckerAgent"),
    # DESIGN
    "ui_agent":       ("agents.design.ui_agent",       "UIAgent"),
    "ux_agent":       ("agents.design.ux_agent",       "UXAgent"),
    "brand_agent":    ("agents.design.brand_agent",    "DesignBrandAgent"),
    "a11y_agent":     ("agents.design.a11y_agent",     "A11yAgent"),
    "prompt_engineer":("agents.design.prompt_engineer", "PromptEngineerAgent"),
}


class TestPipelineImports(unittest.TestCase):
    """Dynamically generated import tests from config.yaml."""

    @classmethod
    def setUpClass(cls):
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            cls.config = yaml.safe_load(f)

    def _get_all_declared_agents(self):
        """Extract flat list of agent names from config.yaml pipelines."""
        pipelines = self.config.get("pipelines", {})
        agents = set()
        for pipeline_name, pipeline_cfg in pipelines.items():
            for agent_name in pipeline_cfg.get("agents", []):
                agents.add(agent_name)
        return agents

    def test_all_declared_agents_importable(self):
        """Every agent name in config.yaml must map to an importable class."""
        declared = self._get_all_declared_agents()
        missing_in_registry = []
        import_errors = []

        for agent_name in sorted(declared):
            if agent_name not in AGENT_REGISTRY:
                missing_in_registry.append(agent_name)
                continue

            module_path, class_name = AGENT_REGISTRY[agent_name]
            try:
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name, None)
                if cls is None:
                    import_errors.append(
                        f"{agent_name}: class '{class_name}' not found in {module_path}"
                    )
            except ImportError as e:
                import_errors.append(f"{agent_name}: ImportError — {e}")

        errors = []
        if missing_in_registry:
            errors.append(
                f"Agents declared in config.yaml but missing in AGENT_REGISTRY: "
                f"{missing_in_registry}"
            )
        if import_errors:
            errors.append("Import failures:\n  " + "\n  ".join(import_errors))

        self.assertFalse(errors, "\n".join(errors))

    def test_all_registry_entries_importable(self):
        """Every entry in AGENT_REGISTRY must be importable (catches stale registry)."""
        import_errors = []
        for agent_name, (module_path, class_name) in AGENT_REGISTRY.items():
            try:
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name, None)
                if cls is None:
                    import_errors.append(
                        f"{agent_name}: class '{class_name}' not in {module_path}"
                    )
            except ImportError as e:
                import_errors.append(f"{agent_name}: ImportError — {e}")

        self.assertFalse(
            import_errors,
            "Stale AGENT_REGISTRY entries:\n  " + "\n  ".join(import_errors),
        )

    def test_config_has_twelve_pipelines(self):
        """config.yaml must declare exactly 12 pipelines."""
        pipelines = self.config.get("pipelines", {})
        self.assertEqual(
            len(pipelines), 12,
            f"Expected 12 pipelines, found {len(pipelines)}: {list(pipelines.keys())}",
        )


if __name__ == "__main__":
    unittest.main()
