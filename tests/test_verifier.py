import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class VerifierTests(unittest.TestCase):
    def test_checkout_beneath_runtime_directory_still_parses_its_sources(self):
        script = Path(__file__).resolve().parents[1] / 'scripts/verify_repository.py'
        spec = importlib.util.spec_from_file_location('isolated_verifier', script)
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / '.research_runtime' / 'clone'
            root.mkdir(parents=True)
            (root / 'broken.py').write_text('def incomplete(', encoding='utf-8')
            with patch.object(verifier, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(verifier.check())


if __name__ == '__main__':
    unittest.main()
