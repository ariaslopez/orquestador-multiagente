"""Tests de integracion ligeros para los pipelines (sin llamadas LLM reales)."""
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestResearchPipeline(unittest.TestCase):
    def test_webscout_returns_empty_on_import_error(self):
        """WebScoutAgent no debe lanzar excepcion si duckduckgo no esta instalado."""
        from agents.research.webscout_agent import WebScoutAgent
        from core.context import AgentContext
        agent = WebScoutAgent()
        ctx = AgentContext(user_input="Bitcoin analysis", session_id="test")
        # Patch llm para que no llame a Groq
        with patch.object(WebScoutAgent, 'llm', new_callable=AsyncMock):
            with patch('agents.research.webscout_agent.DDGS', side_effect=ImportError):
                result = asyncio.run(agent.run(ctx))
        self.assertEqual(result.web_results, [])


class TestDevPipelineUnits(unittest.TestCase):
    def test_planner_extracts_json_from_markdown(self):
        from agents.dev.planner_agent import PlannerAgent
        agent = PlannerAgent()
        text = '```json\n{"project_name": "test", "files": []}\n```'
        result = agent._extract_json(text)
        self.assertIn('project_name', result)

    def test_reviewer_clean_code(self):
        from agents.dev.reviewer_agent import ReviewerAgent
        agent = ReviewerAgent()
        text = '```python\nprint("hello")\n```'
        result = agent._clean_code(text)
        self.assertEqual(result, 'print("hello")')

    def test_coder_clean_code_no_backticks(self):
        from agents.dev.coder_agent import CoderAgent
        agent = CoderAgent()
        text = 'x = 1\nprint(x)'
        result = agent._clean_code(text)
        self.assertEqual(result, 'x = 1\nprint(x)')


class TestPMAgent(unittest.TestCase):
    def test_pm_agent_exists_and_has_name(self):
        from agents.pm_agent import PMAgent
        agent = PMAgent()
        self.assertEqual(agent.name, "PMAgent")


class TestQAAgent(unittest.TestCase):
    def test_qa_agent_pipeline_name(self):
        from agents.qa_agent import QAAgent
        agent = QAAgent()
        self.assertEqual(agent.name, "QAAgent")


class TestTradingAgent(unittest.TestCase):
    def test_trading_agent_exists(self):
        from agents.trading_agent import TradingAnalyticsAgent
        agent = TradingAnalyticsAgent()
        self.assertEqual(agent.name, "TradingAnalyticsAgent")


if __name__ == '__main__':
    unittest.main()
