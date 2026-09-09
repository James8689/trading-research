import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from research_loop.demo import run_demo
from research_loop.__main__ import initialize_runtime

ROOT = Path(__file__).resolve().parents[1]


class EntrypointTests(unittest.TestCase):
    def test_restart_preserves_custom_policy(self):
        with tempfile.TemporaryDirectory() as root:
            initialize_runtime(root, 30, 2)
            value = initialize_runtime(root)
            self.assertEqual(value['policy']['max_tasks'], 30)
            self.assertEqual(value['policy']['max_concurrent'], 2)

    def test_uninitialized_status_error_does_not_prevent_init(self):
        with tempfile.TemporaryDirectory() as root:
            run = subprocess.run([sys.executable, '-m', 'research_loop', '--root', root, 'status'],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn('Traceback', run.stderr)
            self.assertEqual(initialize_runtime(root)['policy']['max_tasks'], 12)

    def test_demo_repeats_without_state_or_model_calls(self):
        first = run_demo()
        self.assertEqual(first, run_demo())
        self.assertEqual(first['research_tasks_completed'], 6)
        self.assertTrue(first['rollback_restored_baseline'])
        self.assertTrue(first['unknown_provider_outcome_blocked'])
        self.assertEqual(first['model_calls'], 0)

    def test_cli_help_and_error(self):
        run = subprocess.run([sys.executable, '-m', 'research_loop', '--help'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        self.assertIn('seed-cef', run.stdout)
        with tempfile.TemporaryDirectory() as root:
            run = subprocess.run([sys.executable, '-m', 'research_loop', '--root', root, 'init'], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['policy']['max_tasks'], 12)


if __name__ == '__main__':
    unittest.main()
