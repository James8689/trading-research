import tempfile
import unittest
from unittest.mock import patch
from research_loop.runner import ResearchLoop, ResearchLoopError


class LegacyGuardTests(unittest.TestCase):
    def test_provider_path_refuses_before_claim_or_subprocess(self):
        with tempfile.TemporaryDirectory() as root:
            loop = ResearchLoop(root)
            with patch('research_loop.runner.subprocess.run') as process:
                with self.assertRaises(ResearchLoopError):
                    loop.run(backend='codex')
                with self.assertRaises(ResearchLoopError):
                    loop._dispatch_codex({}, '', {})
                process.assert_not_called()


if __name__ == '__main__':
    unittest.main()
