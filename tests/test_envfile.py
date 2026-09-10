import os
import tempfile
import unittest
from pathlib import Path

from research_loop.envfile import (
    env_state, load_env_file, merged_env, parse_env_text, usd_to_micro, write_env_values,
)
from research_loop.routing import catalog_models, parse_model_list, suggested_stack


class EnvWriteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('OPENAI_API_KEY', 'OPENAI_MODEL', 'ROLE_RESEARCHER', 'XAI_API_KEY', 'PROVIDER_MUSE_API_KEY'):
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

    def test_writes_custom_provider_keys(self):
        saved = write_env_values(self.root, {
            'RESEARCH_PROVIDERS': 'muse',
            'PROVIDER_MUSE_KIND': 'openai',
            'PROVIDER_MUSE_BASE_URL': 'https://api.together.xyz/v1',
            'PROVIDER_MUSE_API_KEY': 'sk-muse-4242',
            'PROVIDER_MUSE_MODEL': 'muse-spark',
        })
        self.assertEqual(self.env()['PROVIDER_MUSE_MODEL'], 'muse-spark')
        self.assertIsNone(next(row for row in saved if row['key'] == 'PROVIDER_MUSE_API_KEY')['value'])
        self.assertEqual(next(row for row in saved if row['key'] == 'PROVIDER_MUSE_API_KEY')['hint'], '4242')

    def test_refuses_locked_and_unknown_keys(self):
        for key in ('DASHBOARD_PASSWORD', 'RESEARCH_BUDGET_LIMIT_USD', 'PATH'):
            with self.assertRaises(ValueError):
                write_env_values(self.root, {key: 'x'})
        self.assertFalse((self.root / '.env').exists())

    def test_refuses_values_that_would_break_the_file(self):
        write_env_values(self.root, {'OPENAI_API_KEY': ' sk-live-\n9999 '})
        self.assertEqual(self.env()['OPENAI_API_KEY'], 'sk-live-9999')
        with self.assertRaises(ValueError):
            write_env_values(self.root, {'OPENAI_API_KEY': 'has"quote'})
        with self.assertRaises(ValueError):
            write_env_values(self.root, {'OPENAI_MODEL': 'a' * 401})
        with self.assertRaises(ValueError):
            write_env_values(self.root, {'OPENAI_API_KEY': 'a' * 8193})

    def test_env_state_never_returns_a_secret(self):
        state = env_state({'OPENAI_API_KEY': 'sk-abcd1234', 'OPENAI_MODEL': 'gpt-5.4'}, self.root)
        by_key = {row['key']: row for row in state['writable']}
        self.assertEqual(by_key['OPENAI_API_KEY'], {
            'key': 'OPENAI_API_KEY', 'secret': True, 'set': True, 'value': None, 'hint': '1234'})
        self.assertEqual(by_key['OPENAI_MODEL']['value'], 'gpt-5.4')
        muse = env_state({
            'PROVIDER_MUSE_API_KEY': 'sk-muse-7777',
            'PROVIDER_MUSE_BASE_URL': 'https://api.meta.ai/v1',
        }, self.root)
        by_muse = {row['key']: row for row in muse['writable']}
        self.assertTrue(by_muse['PROVIDER_MUSE_API_KEY']['set'])
        self.assertIsNone(by_muse['PROVIDER_MUSE_API_KEY']['value'])
        self.assertEqual(by_muse['PROVIDER_MUSE_API_KEY']['hint'], '7777')
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


class ModelCatalogTests(unittest.TestCase):
    def test_parse_and_dedupe(self):
        items = parse_model_list('openai:gpt-5.4, xai:grok-4, openai:gpt-5.4')
        self.assertEqual([i['spec'] for i in items], ['openai:gpt-5.4', 'xai:grok-4'])
        with self.assertRaises(ValueError):
            parse_model_list('notaprovider:x')

    def test_catalog_unions_defaults_roles_and_list(self):
        env = {
            'RESEARCH_MODELS': 'openai:gpt-4o-mini',
            'OPENAI_MODEL': 'gpt-5.4',
            'ROLE_REVIEWER': 'anthropic:claude-sonnet-4-6',
            'ANTHROPIC_API_KEY': 'sk-abcd1234',
        }
        specs = [item['spec'] for item in catalog_models(env)]
        self.assertEqual(specs, ['openai:gpt-4o-mini', 'openai:gpt-5.4', 'anthropic:claude-sonnet-4-6'])
        sonnet = next(item for item in catalog_models(env) if item['provider'] == 'anthropic')
        self.assertEqual(sonnet['key_hint'], '1234')

    def test_custom_provider_is_a_first_class_route(self):
        env = {
            'RESEARCH_PROVIDERS': 'muse',
            'PROVIDER_MUSE_KIND': 'openai',
            'PROVIDER_MUSE_BASE_URL': 'https://api.together.xyz/v1',
            'PROVIDER_MUSE_API_KEY': 'sk-muse-9999',
            'PROVIDER_MUSE_MODEL': 'muse-spark',
            'RESEARCH_MODELS': 'muse:muse-spark',
        }
        items = parse_model_list('muse:muse-spark', env)
        self.assertEqual(items[0]['spec'], 'muse:muse-spark')
        catalog = catalog_models(env)
        self.assertEqual(catalog[0]['key_hint'], '9999')
        self.assertEqual(parse_model_list('muse:muse-spark', {})[0]['spec'], 'muse:muse-spark')
        with self.assertRaises(ValueError):
            parse_model_list('unknownhost:x', {})

    def test_suggested_stack_marks_what_is_already_added(self):
        rows = suggested_stack({'RESEARCH_MODELS': 'xai:grok-4', 'XAI_API_KEY': 'x'})
        by_id = {row['id']: row for row in rows}
        self.assertTrue(by_id['grok']['in_catalog'])
        self.assertTrue(by_id['grok']['has_key'])
        self.assertFalse(by_id['sol']['in_catalog'])
        self.assertFalse(by_id['sol']['has_key'])
        self.assertFalse(by_id['astra']['in_catalog'])
        leftover = {row['id']: row for row in suggested_stack({
            'RESEARCH_MODELS': 'openai:gpt-5.4,xai:grok-4',
            'ROLE_DIRECTOR_PLAN': 'openai:gpt-5.4',
            'ROLE_DATA_AUDITOR': 'xai:grok-4',
        })}
        self.assertTrue(leftover['sol']['in_catalog'])
        self.assertFalse(leftover['sol']['has_key'])
        self.assertEqual(leftover['sol']['spec'], 'openai:gpt-5.4')
        self.assertEqual(by_id['sol']['provider'], 'openai')
        self.assertEqual(by_id['astra']['provider'], 'openai')
        self.assertEqual(by_id['sol']['preference'], 'GPT-5.6 Sol')
        self.assertEqual(by_id['astra']['preference'], 'GPT-6 Astra')
        self.assertEqual(by_id['muse']['roles'], ('researcher',))
        self.assertEqual(by_id['muse']['provider'], 'muse')
        self.assertTrue(by_id['muse']['custom'])
        self.assertEqual(by_id['astra']['model'], 'gpt-6-astra')
        self.assertEqual(by_id['sol']['model'], 'gpt-5.6-sol')

    def test_two_openai_models_are_distinct_stack_rows(self):
        env = {
            'RESEARCH_MODELS': 'openai:sol-id,openai:astra-id',
            'ROLE_DIRECTOR_PLAN': 'openai:sol-id',
            'ROLE_DIRECTOR_DECISION': 'openai:sol-id',
            'ROLE_IMPROVEMENT_PROPOSAL': 'openai:sol-id',
            'OPENAI_API_KEY': 'x',
        }
        by_id = {row['id']: row for row in suggested_stack(env)}
        self.assertTrue(by_id['sol']['in_catalog'])
        self.assertTrue(by_id['astra']['in_catalog'])
        specs = [item['spec'] for item in catalog_models(env)]
        self.assertEqual(specs, ['openai:sol-id', 'openai:astra-id'])
        one = suggested_stack({
            'RESEARCH_MODELS': 'openai:sol-id',
            'ROLE_DIRECTOR_PLAN': 'openai:sol-id',
        })
        one_ids = {row['id']: row for row in one}
        self.assertTrue(one_ids['sol']['in_catalog'])
        self.assertFalse(one_ids['astra']['in_catalog'])
