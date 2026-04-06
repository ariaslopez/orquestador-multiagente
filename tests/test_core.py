"""Tests unitarios del core: BaseAgent, Context, SecurityLayer, MemoryManager."""
import os
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBaseAgent(unittest.TestCase):
    def setUp(self):
        from core.base_agent import BaseAgent
        from core.context import AgentContext

        class DummyAgent(BaseAgent):
            name = "DummyAgent"
            description = "Agente de prueba"
            async def run(self, context):
                context.final_output = "dummy_output"
                return context

        self.AgentClass = DummyAgent
        self.context_class = AgentContext

    def test_agent_has_name(self):
        agent = self.AgentClass()
        self.assertEqual(agent.name, "DummyAgent")

    def test_agent_run_returns_context(self):
        agent = self.AgentClass()
        ctx = self.context_class(user_input="test", session_id="sess-1")
        result = asyncio.run(agent.run(ctx))
        self.assertEqual(result.final_output, "dummy_output")

    def test_agent_log(self):
        agent = self.AgentClass()
        ctx = self.context_class(user_input="test", session_id="sess-1")
        agent.log(ctx, "mensaje de log")
        self.assertIn("mensaje de log", ctx.agent_logs.get("DummyAgent", []))


class TestAgentContext(unittest.TestCase):
    def setUp(self):
        from core.context import AgentContext
        self.AgentContext = AgentContext

    def test_context_creation(self):
        ctx = self.AgentContext(user_input="hola", session_id="abc")
        self.assertEqual(ctx.user_input, "hola")
        self.assertEqual(ctx.session_id, "abc")
        self.assertIsNone(ctx.final_output)

    def test_context_stores_plan(self):
        ctx = self.AgentContext(user_input="test", session_id="abc")
        ctx.plan = {"files": [], "stack": ["python"]}
        self.assertEqual(ctx.plan["stack"], ["python"])

    def test_context_agent_logs_default_empty(self):
        ctx = self.AgentContext(user_input="test", session_id="abc")
        self.assertIsInstance(ctx.agent_logs, dict)


class TestSecurityLayer(unittest.TestCase):
    def setUp(self):
        from infrastructure.security_layer import SecurityLayer
        self.sec = SecurityLayer

    def test_valid_path_allowed(self):
        ok, reason = self.sec.validate_path("output/project/main.py")
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_system_path_blocked(self):
        ok, reason = self.sec.validate_path("/etc/passwd")
        self.assertFalse(ok)
        self.assertIn("bloqueado", reason.lower())

    def test_pip_command_allowed(self):
        ok, reason = self.sec.validate_command("pip install requests")
        self.assertTrue(ok)

    def test_rm_command_blocked(self):
        ok, reason = self.sec.validate_command("rm -rf /")
        self.assertFalse(ok)

    def test_secret_detection(self):
        findings = self.sec.scan_secrets('API_KEY = "sk-abc123456789abcdef"')
        self.assertTrue(len(findings) > 0)

    def test_clean_content_no_findings(self):
        findings = self.sec.scan_secrets('x = 1 + 2\nprint(x)')
        self.assertEqual(findings, [])


class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        os.environ['SQLITE_DB_PATH'] = '/tmp/test_claw_memory.db'
        from infrastructure.memory_manager import MemoryManager
        self.memory = MemoryManager()

    def tearDown(self):
        Path('/tmp/test_claw_memory.db').unlink(missing_ok=True)

    def test_create_session_returns_uuid(self):
        sid = self.memory.create_session("test task", "dev")
        self.assertIsInstance(sid, str)
        self.assertEqual(len(sid), 36)  # UUID formato

    def test_get_sessions_returns_list(self):
        self.memory.create_session("task 1", "dev")
        self.memory.create_session("task 2", "research")
        sessions = self.memory.get_all_sessions(limit=10)
        self.assertGreaterEqual(len(sessions), 2)

    def test_update_session(self):
        sid = self.memory.create_session("update test", "qa")
        self.memory.update_session(sid, status='completed', total_tokens=500)
        sessions = self.memory.get_all_sessions(limit=1)
        found = next((s for s in sessions if s['session_id'] == sid), None)
        self.assertIsNotNone(found)
        self.assertEqual(found['status'], 'completed')

    def test_save_checkpoint(self):
        sid = self.memory.create_session("checkpoint test", "dev")
        self.memory.save_checkpoint(sid, "PlannerAgent", {"step": 1, "data": "abc"})
        # No debe lanzar excepcion

    def test_get_usage_stats(self):
        stats = self.memory.get_usage_stats()
        self.assertIsInstance(stats, dict)


if __name__ == '__main__':
    unittest.main()
