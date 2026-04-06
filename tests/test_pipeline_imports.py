"""Regression test: every agent declared in config.yaml must be importable.

This test acts as a guard against config/code drift:
if a pipeline declares an agent that doesn't exist as a Python class,
the test fails immediately — before any runtime error in production.

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
    # CONTENT / OFFICE / QA / TRADING / PM
    "content":  ("agents.content_agent",  "ContentAgent"),
    "office":   ("agents.office_agent",   "OfficeAgent"),
    "qa":       ("agents.qa_agent",       "QAAgent"),
    "trading":  ("agents.trading_agent",  "TradingAnalyticsAgent"),
    "pm":       ("agents.pm_agent",       "PMAgent"),
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

    def test_config_has_seven_pipelines(self):
        """config.yaml must declare exactly 7 pipelines."""
        pipelines = self.config.get("pipelines", {})
        self.assertEqual(
            len(pipelines), 7,
            f"Expected 7 pipelines, found {len(pipelines)}: {list(pipelines.keys())}",
        )


if __name__ == "__main__":
    unittest.main()
