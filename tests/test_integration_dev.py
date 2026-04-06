"""Integration test for the DEV pipeline (mocked LLM).

Runs the full DEV pipeline chain:
  Planner -> Coder -> Reviewer -> Security -> Executor -> Git

All LLM calls are mocked so this test:
- Does NOT require API keys
- Does NOT make network calls
- Validates that the pipeline produces the expected context shape

Run: pytest tests/test_integration_dev.py -v
"""
import sys
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
import os
os.environ["SQLITE_DB_PATH"] = "/tmp/test_dev_integration.db"

# Fake LLM responses per agent
FAKE_PLAN = json.dumps({
    "project_name": "trading_api",
    "stack": "Python/FastAPI",
    "files": [
        {"path": "main.py", "description": "FastAPI entry point"},
        {"path": "requirements.txt", "description": "Dependencies"},
    ],
})

FAKE_CODE = """# main.py\nfrom fastapi import FastAPI\napp = FastAPI()\n
@app.get('/')\ndef root():\n    return {'status': 'ok'}\n"""

FAKE_REVIEW = "Code review complete. No critical bugs found. Minor: add docstrings."
FAKE_SECURITY = "Security check passed. No hardcoded credentials. No SQL injection vectors."


def make_llm_response(content: str):
    """Build a minimal object mimicking Groq/Gemini API response."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


class TestDevPipelineIntegration(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.tmpdir = tempfile.mkdtemp()

    async def asyncTearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        Path("/tmp/test_dev_integration.db").unlink(missing_ok=True)

    async def _run_pipeline(self):
        """Run the full DEV pipeline with mocked LLM responses."""
        from core.context import AgentContext
        from agents.dev.planner_agent import PlannerAgent
        from agents.dev.coder_agent import CoderAgent
        from agents.dev.reviewer_agent import ReviewerAgent
        from agents.dev.security_agent import SecurityAgent
        from agents.dev.executor_agent import ExecutorAgent
        from agents.dev.git_agent import GitAgent

        ctx = AgentContext(
            user_input="Crea una API REST en FastAPI para señales de trading",
            task_type="dev",
            session_id="test-dev-integration",
            output_dir=self.tmpdir,
        )

        # Mock LLM at the api_router level
        responses = [
            make_llm_response(FAKE_PLAN),
            make_llm_response(FAKE_CODE),
            make_llm_response(FAKE_REVIEW),
            make_llm_response(FAKE_SECURITY),
        ]
        call_count = {"n": 0}

        async def mock_complete(*args, **kwargs):
            idx = min(call_count["n"], len(responses) - 1)
            call_count["n"] += 1
            return responses[idx]

        with patch("core.api_router.APIRouter.complete", side_effect=mock_complete):
            # Also mock file writing in executor to avoid disk side-effects
            with patch("agents.dev.executor_agent.ExecutorAgent._write_files",
                       new_callable=AsyncMock) as mock_write:
                mock_write.return_value = ["main.py", "requirements.txt"]

                planner = PlannerAgent()
                coder = CoderAgent()
                reviewer = ReviewerAgent()
                security_agent = SecurityAgent()
                executor = ExecutorAgent()
                git = GitAgent()

                ctx = await planner.run(ctx)
                ctx = await coder.run(ctx)
                ctx = await reviewer.run(ctx)
                ctx = await security_agent.run(ctx)
                ctx = await executor.run(ctx)
                ctx = await git.run(ctx)

        return ctx

    async def test_pipeline_produces_project_name(self):
        ctx = await self._run_pipeline()
        self.assertTrue(
            hasattr(ctx, "project_name") and ctx.project_name,
            "DEV pipeline must set ctx.project_name",
        )

    async def test_pipeline_produces_generated_files(self):
        ctx = await self._run_pipeline()
        self.assertTrue(
            hasattr(ctx, "generated_files") and ctx.generated_files,
            "DEV pipeline must populate ctx.generated_files",
        )

    async def test_pipeline_produces_review_output(self):
        ctx = await self._run_pipeline()
        has_review = (
            hasattr(ctx, "review_output") and ctx.review_output
            or hasattr(ctx, "code_review") and ctx.code_review
        )
        self.assertTrue(has_review, "DEV pipeline must produce a review output")

    async def test_pipeline_produces_security_output(self):
        ctx = await self._run_pipeline()
        has_security = (
            hasattr(ctx, "security_output") and ctx.security_output
            or hasattr(ctx, "security_check") and ctx.security_check
        )
        self.assertTrue(has_security, "DEV pipeline must produce a security output")

    async def test_context_has_task_type(self):
        ctx = await self._run_pipeline()
        self.assertEqual(ctx.task_type, "dev")

    async def test_git_agent_runs_without_crash(self):
        """GitAgent stub must not raise even without a git_repo in context."""
        ctx = await self._run_pipeline()
        # If we get here, GitAgent didn't crash
        self.assertIsNotNone(ctx)


if __name__ == "__main__":
    unittest.main()
