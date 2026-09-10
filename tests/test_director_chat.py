import json
import shutil
import tempfile
import unittest
from pathlib import Path

from research_loop.__main__ import initialize_runtime, seed_cef
from research_loop.budget import BudgetLedger
from research_loop.director_chat import talk
from research_loop.dispatch import apply_env_budget
from research_loop.network import Network

ROOT = Path(__file__).resolve().parents[1]


class DirectorChatTests(unittest.TestCase):
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
        self.env = {
            'RESEARCH_BUDGET_PERIOD': 'local-test',
            'RESEARCH_BUDGET_LIMIT_USD': '10',
            'RESEARCH_MAX_CALL_USD': '0.50',
            'OPENAI_API_KEY': 'sk-test-1234',
            'ROLE_DIRECTOR_PLAN': 'openai:gpt-test',
        }
        apply_env_budget(BudgetLedger(self.root), self.env)

    def test_plain_reply_without_tools(self):
        def transport(url, headers, body, timeout):
            self.assertNotIn('response_format', body)
            self.assertTrue(body.get('tools'))
            return 200, {
                'id': 'cmpl-chat',
                'choices': [{'message': {'content': 'Queue is waiting on director_plan. Nothing has run.'}}],
                'usage': {'prompt_tokens': 20, 'completion_tokens': 12},
            }

        value = talk(self.root, 'What is going on?', env=self.env, transport=transport)
        self.assertTrue(value['ok'])
        self.assertIn('director_plan', value['reply'])
        self.assertEqual(value['tools'], [])
        self.assertEqual(value['model'], 'gpt-test')

    def test_status_tool_then_reply(self):
        round_id = {'n': 0}

        def transport(url, headers, body, timeout):
            round_id['n'] += 1
            if round_id['n'] == 1:
                return 200, {
                    'id': 'cmpl-tool',
                    'choices': [{'message': {
                        'content': '',
                        'tool_calls': [{
                            'id': 'call_status',
                            'type': 'function',
                            'function': {'name': 'get_status', 'arguments': '{}'},
                        }],
                    }}],
                    'usage': {'prompt_tokens': 10, 'completion_tokens': 4},
                }
            return 200, {
                'id': 'cmpl-final',
                'choices': [{'message': {'content': 'Six tasks are waiting. Spend is open. Next action is director_plan.'}}],
                'usage': {'prompt_tokens': 30, 'completion_tokens': 20},
            }

        value = talk(self.root, 'Give me an update.', env=self.env, transport=transport)
        self.assertEqual(value['tools'][0]['name'], 'get_status')
        self.assertIsNone(value['tools'][0]['error'])
        self.assertIn('Six tasks', value['reply'])
        self.assertEqual(round_id['n'], 2)
