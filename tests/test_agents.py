"""Tests unitarios de los agentes: DEV, Research, Content, Office."""
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPlannerAgent(unittest.TestCase):
    def setUp(self):
        from agents.dev.planner_agent import PlannerAgent
        from core.context import AgentContext
        self.agent = PlannerAgent()
        self.Context = AgentContext

    @patch.object(__import__('core.base_agent', fromlist=['BaseAgent']).BaseAgent, 'llm',
                  new_callable=AsyncMock)
    def test_run_returns_context_with_plan(self, mock_llm):
        mock_llm.return_value = '{"project_name": "test-api", "files": [{"path": "main.py", "description": "entry", "priority": 1}], "stack": ["python"], "install_commands": [], "run_command": "python main.py"}'
        ctx = self.Context(user_input="Crea una API REST", session_id="test-1")
        result = asyncio.run(self.agent.run(ctx))
        self.assertIsNotNone(result.plan)
        self.assertIn('files', result.plan)


class TestLanguageAgent(unittest.TestCase):
    def setUp(self):
        from agents.language_agent import LanguageAgent
        from core.context import AgentContext
        self.agent = LanguageAgent()
        self.Context = AgentContext

    def test_detects_python(self):
        ctx = self.Context(user_input="analiza este archivo .py de flask", session_id="t1")
        result = asyncio.run(self.agent.run(ctx))
        self.assertIsNotNone(result)


class TestContentAgentPersonalities(unittest.TestCase):
    def test_all_personalities_exist(self):
        from agents.content_agent import PERSONALITIES
        for key in ['analyst', 'trader', 'educator', 'bullish', 'neutral']:
            self.assertIn(key, PERSONALITIES)
            self.assertIsInstance(PERSONALITIES[key], str)
            self.assertGreater(len(PERSONALITIES[key]), 10)


class TestOfficeAgentReadCSV(unittest.TestCase):
    def setUp(self):
        import tempfile
        import csv
        self.tmp = tempfile.NamedTemporaryFile(suffix='.csv', mode='w',
                                               delete=False, newline='')
        writer = csv.DictWriter(self.tmp, fieldnames=['date', 'pnl', 'trades'])
        writer.writeheader()
        writer.writerows([
            {'date': '2026-01-01', 'pnl': '150.5', 'trades': '12'},
            {'date': '2026-01-02', 'pnl': '-30.2', 'trades': '8'},
        ])
        self.tmp.close()
        self.csv_path = self.tmp.name

    def tearDown(self):
        Path(self.csv_path).unlink(missing_ok=True)

    def test_read_csv_returns_content(self):
        from agents.office_agent import OfficeAgent
        agent = OfficeAgent()
        content = agent._read_file(self.csv_path, '.csv')
        self.assertIn('date', content)
        self.assertIn('pnl', content)


class TestSecurityAgentPatterns(unittest.TestCase):
    def test_detects_eval(self):
        from agents.dev.security_agent import SecurityAgent, SECURITY_PATTERNS
        patterns = [p[0] for p in SECURITY_PATTERNS]
        self.assertIn('eval(', patterns)
        self.assertIn('exec(', patterns)
        self.assertIn('shell=True', patterns)

    def test_no_false_positive_clean_code(self):
        from agents.dev.security_agent import SecurityAgent, SECURITY_PATTERNS
        clean_code = 'def add(a, b):\n    return a + b\n'
        findings = [p for p, _ in SECURITY_PATTERNS if p.upper() in clean_code.upper()]
        self.assertEqual(findings, [])


if __name__ == '__main__':
    unittest.main()
