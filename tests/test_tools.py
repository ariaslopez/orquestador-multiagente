"""Tests unitarios de tools: SafeFileSystem, WebSearch, GitAgent."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ['SQLITE_DB_PATH'] = '/tmp/test_tools_claw.db'


class TestSafeFileSystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from tools.safe_filesystem import SafeFileSystem
        self.fs = SafeFileSystem(base_dir=self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        Path('/tmp/test_tools_claw.db').unlink(missing_ok=True)

    def test_write_and_read(self):
        path = self.fs.write('subdir/test.py', 'print("hello")', actor='test')
        self.assertTrue(path.exists())
        content = self.fs.read('subdir/test.py')
        self.assertEqual(content, 'print("hello")')

    def test_list_dir(self):
        self.fs.write('a.py', 'pass', actor='test')
        self.fs.write('sub/b.py', 'pass', actor='test')
        files = self.fs.list_dir()
        self.assertIn('a.py', files)
        self.assertIn(str(Path('sub/b.py')), files)

    def test_delete(self):
        self.fs.write('del_me.txt', 'content', actor='test')
        self.fs.delete('del_me.txt', actor='test')
        self.assertFalse((Path(self.tmpdir) / 'del_me.txt').exists())

    def test_blocked_path_raises(self):
        from tools.safe_filesystem import SafeFileSystem
        # Intento de escribir fuera del base_dir via path traversal
        with self.assertRaises(PermissionError):
            self.fs.write('../../etc/passwd', 'hack', actor='attacker')


class TestAuditLogger(unittest.TestCase):
    def setUp(self):
        self.tmplog = tempfile.NamedTemporaryFile(suffix='.log', delete=False)
        self.tmplog.close()
        os.environ['AUDIT_LOG_PATH'] = self.tmplog.name
        from infrastructure.audit_logger import AuditLogger
        self.logger = AuditLogger()

    def tearDown(self):
        Path(self.tmplog.name).unlink(missing_ok=True)

    def test_log_writes_entry(self):
        self.logger.log('TEST', 'agent', 'test_action', 'target', 'ok')
        logs = self.logger.get_recent_logs(limit=10)
        self.assertGreater(len(logs), 0)
        self.assertEqual(logs[-1]['event_type'], 'TEST')

    def test_log_security_violation(self):
        self.logger.log_security_violation('TestAgent', 'PATH_VIOLATION', '/etc')
        logs = self.logger.get_recent_logs()
        last = logs[-1]
        self.assertEqual(last['result'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
