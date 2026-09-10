import os
import tempfile
import unittest
from pathlib import Path

from research_loop.envfile import (
    env_state, load_env_file, merged_env, parse_env_text, usd_to_micro, write_env_values,
)


class EnvWriteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('OPENAI_API_KEY', 'OPENAI_MODEL', 'ROLE_RESEARCHER', 'XAI_API_KEY'):
            os.environ.pop(name, None)
            self.addCleanup(os.environ.pop, name, None)

    def env(self):
        return load_env_file(self.root / '.env')

    def test_creates_file_and_updates_process_env(self):
        saved = write_env_values(self.root, {'OPENAI_API_KEY': 'sk-test-1234'})
        self.assertEqual(self.env()['OPENAI_API_KEY'], 'sk-test-1234')
        self.assertEqual(os.environ['OPENAI_API_KEY'], 'sk-test-1234')
        self.assertEqual(saved[0]['hint'], '1234')
        self.assertIsNone(saved[0]['value'])

    def test_preserves_comments_and_rewrites_duplicates(self):
        (self.root / '.env').write_text(
            '# keep me\nOPENAI_API_KEY=old\nOTHER=untouched\nOPENAI_API_KEY=stale\n', encoding='utf-8')
        write_env_values(self.root, {'OPENAI_API_KEY': 'new'})
        text = (self.root / '.env').read_text(encoding='utf-8')
        self.assertIn('# keep me', text)
        self.assertIn('OTHER=untouched', text)
        self.assertNotIn('stale', text)
        self.assertEqual(self.env()['OPENAI_API_KEY'], 'new')

    def test_empty_value_clears_the_variable(self):
        write_env_values(self.root, {'XAI_API_KEY': 'sk-x'})
        write_env_values(self.root, {'XAI_API_KEY': ''})
        self.assertEqual(self.env()['XAI_API_KEY'], '')
        self.assertNotIn('XAI_API_KEY', os.environ)

    def test_refuses_locked_and_unknown_keys(self):
        for key in ('DASHBOARD_PASSWORD', 'RESEARCH_BUDGET_LIMIT_USD', 'PATH'):
            with self.assertRaises(ValueError):
                write_env_values(self.root, {key: 'x'})
        self.assertFalse((self.root / '.env').exists())

    def test_refuses_values_that_would_break_the_file(self):
        for value in ('line\nROLE_RESEARCHER=openai:x', 'has"quote', 'a' * 401):
            with self.assertRaises(ValueError):
                write_env_values(self.root, {'OPENAI_API_KEY': value})

    def test_env_state_never_returns_a_secret(self):
        state = env_state({'OPENAI_API_KEY': 'sk-abcd1234', 'OPENAI_MODEL': 'gpt-5.4'}, self.root)
        by_key = {row['key']: row for row in state['writable']}
        self.assertEqual(by_key['OPENAI_API_KEY'], {
            'key': 'OPENAI_API_KEY', 'secret': True, 'set': True, 'value': None, 'hint': '1234'})
        self.assertEqual(by_key['OPENAI_MODEL']['value'], 'gpt-5.4')
        self.assertIn('DASHBOARD_PASSWORD', state['locked'])


class EnvfileTests(unittest.TestCase):
    def test_parse_and_process_env_wins(self):
        parsed = parse_env_text('OPENAI_API_KEY=from-file\n# c\nROLE_RESEARCHER="xai:grok-4"\n')
        self.assertEqual(parsed['OPENAI_API_KEY'], 'from-file')
        self.assertEqual(parsed['ROLE_RESEARCHER'], 'xai:grok-4')
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / '.env').write_text('OPENAI_API_KEY=file\nXAI_API_KEY=x\n', encoding='utf-8')
            merged = merged_env(root, {'OPENAI_API_KEY': 'process'})
            self.assertEqual(merged['OPENAI_API_KEY'], 'process')
            self.assertEqual(merged['XAI_API_KEY'], 'x')
            self.assertEqual(load_env_file(root / 'missing'), {})

    def test_usd_to_micro(self):
        self.assertEqual(usd_to_micro('10'), 10_000_000)
        self.assertEqual(usd_to_micro('0.50'), 500_000)
        with self.assertRaises(ValueError):
            usd_to_micro('-1')
