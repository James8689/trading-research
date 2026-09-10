import json
import shutil
import tempfile
import unittest
from pathlib import Path

from research_loop.__main__ import initialize_runtime, seed_cef
from research_loop.dispatch import apply_env_budget, dispatch_next
from research_loop.budget import BudgetLedger
from research_loop.network import Network

ROOT = Path(__file__).resolve().parents[1]


def _result(decision='blocked'):
    return {
        'summary': 'Original contractual source has not been supplied.',
        'decision': decision,
        'evidence': [],
        'uncertainty': 'No filings ingested.',
        'next_action': 'Obtain original terms.',
        'memory': 'Participation remains unknown.',
    }


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        batch = self.root / 'research_batch3'
        batch.mkdir()
        shutil.copy(ROOT / 'research_batch3' / 'frozen_experiment_plans.json', batch)
        shutil.copy(ROOT / 'research_batch3' / 'freeze_receipt.json', batch)
        (self.root / 'agents').mkdir()
        shutil.copytree(ROOT / 'agents' / 'network', self.root / 'agents' / 'network')
        initialize_runtime(self.root)
        seed_cef(self.root, Network(self.root), [])

    def test_placeholder_budget_replaced_then_fake_dispatch(self):
        env = {
            'RESEARCH_BUDGET_PERIOD': 'local-test',
            'RESEARCH_BUDGET_LIMIT_USD': '10',
            'RESEARCH_MAX_CALL_USD': '0.50',
            'OPENAI_API_KEY': 'sk-test-1234',
            'ROLE_DIRECTOR_PLAN': 'openai:gpt-test',
        }
        note = apply_env_budget(BudgetLedger(self.root), env)
        self.assertTrue(note['applied'])
        self.assertEqual(note['period_id'], 'local-test')

        def transport(url, headers, body, timeout):
            self.assertIn('chat/completions', url)
            self.assertTrue(headers['Authorization'].startswith('Bearer '))
            payload = {
                'id': 'cmpl-fake',
                'choices': [{'message': {'content': json.dumps(_result())}}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 5},
            }
            return 200, payload

        value = dispatch_next(self.root, env=env, transport=transport)
        self.assertEqual(value['role'], 'director_plan')
        self.assertEqual(value['model'], 'gpt-test')
        self.assertEqual(value['result']['decision'], 'blocked')
        self.assertEqual(value['budget']['state'], 'settled')
        self.assertFalse(BudgetLedger(self.root).status()['blocked'])

    def test_refuses_without_key_or_budget(self):
        with self.assertRaises(RuntimeError):
            dispatch_next(self.root, env={'ROLE_DIRECTOR_PLAN': 'openai:gpt-test', 'OPENAI_API_KEY': ''})
