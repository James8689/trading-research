import http.cookiejar
import json
import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

from dashboard.server import make_server
from research_loop.__main__ import initialize_runtime

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = 'test-operator-password'


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        batch = self.root / 'research_batch3'
        batch.mkdir()
        shutil.copy(ROOT / 'research_batch3' / 'frozen_experiment_plans.json', batch)
        shutil.copy(ROOT / 'research_batch3' / 'freeze_receipt.json', batch)
        initialize_runtime(self.root)
        self.httpd = make_server(self.root, '127.0.0.1', 0, PASSWORD)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._stop)
        self.cookies = http.cookiejar.CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookies))

    def _stop(self):
        httpd = getattr(self, 'httpd', None)
        if httpd is None:
            return
        try:
            httpd.shutdown()
            httpd.server_close()
        except OSError:
            pass
        self.httpd = None

    def url(self, path):
        return f'http://127.0.0.1:{self.port}{path}'

    def call(self, path, payload=None, method=None, csrf=None, status=200):
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode()
            headers['Content-Type'] = 'application/json'
            method = method or 'POST'
        if csrf:
            headers['X-CSRF-Token'] = csrf
        req = Request(self.url(path), data=data, headers=headers, method=method or 'GET')
        try:
            with self.opener.open(req) as response:
                body = json.loads(response.read().decode())
                self.assertEqual(response.status, status)
                return body
        except HTTPError as exc:
            body = json.loads(exc.read().decode())
            if exc.code != status:
                self.fail(f'{path} expected {status} got {exc.code}: {body}')
            return body

    def login(self):
        body = self.call('/api/login', {'password': PASSWORD})
        self.assertTrue(body['ok'])
        return body['csrf']

    def test_requires_login(self):
        self.call('/api/overview', status=401)

    def test_wrong_password(self):
        self.call('/api/login', {'password': 'nope'}, status=401)

    def test_overview_and_csrf(self):
        csrf = self.login()
        me = self.call('/api/me')
        self.assertEqual(me['csrf'], csrf)
        overview = self.call('/api/overview')
        self.assertEqual(overview['mode'], 'assisted_manual')
        self.assertFalse(overview['provider_dispatch'])
        self.assertFalse(overview['broker_execution'])
        self.assertTrue(overview['budget']['blocked'])
        self.assertTrue(overview['freeze']['ok'])

    def test_messages_and_seed_persist_across_restart(self):
        csrf = self.login()
        sent = self.call('/api/messages', {'body': 'Investigate B3-H1-v1 filings first.'}, csrf=csrf)
        self.assertEqual(sent['message']['author'], 'james')
        self.assertEqual(sent['reply']['author'], 'director')
        seeded = self.call('/api/control/seed-cef', {}, csrf=csrf)
        self.assertIn('cycle_id', seeded)
        families = self.call('/api/families')
        self.assertEqual(families['families'][0]['candidate_id'], 'B3-H1-v1')
        self._stop()
        self.httpd = make_server(self.root, '127.0.0.1', 0, PASSWORD)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.cookies = http.cookiejar.CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookies))
        csrf = self.login()
        inbox = self.call('/api/messages')
        bodies = [m['body'] for m in inbox['messages']]
        self.assertIn('Investigate B3-H1-v1 filings first.', bodies)
        overview = self.call('/api/overview')
        self.assertEqual(overview['cycles'][0]['cycle_id'], seeded['cycle_id'])
        self.assertEqual(overview['families']['families'][0]['candidate_id'], 'B3-H1-v1')

    def test_env_key_saved_to_file_and_never_returned(self):
        csrf = self.login()
        for name in ('OPENAI_API_KEY', 'OPENAI_MODEL', 'ROLE_RESEARCHER'):
            self.addCleanup(os.environ.pop, name, None)
        saved = self.call('/api/env', {'values': {
            'OPENAI_API_KEY': 'sk-live-9999', 'OPENAI_MODEL': 'gpt-5.4',
            'ROLE_RESEARCHER': 'openai:gpt-5.4',
        }}, csrf=csrf)
        body = json.dumps(saved)
        self.assertNotIn('sk-live-9999', body)
        self.assertIn('9999', body)
        text = (self.root / '.env').read_text(encoding='utf-8')
        self.assertIn('OPENAI_API_KEY=sk-live-9999', text)
        view = self.call('/api/env')
        self.assertNotIn('sk-live-9999', json.dumps(view))
        route = next(r for r in view['routes'] if r['role'] == 'researcher')
        self.assertEqual((route['provider'], route['model'], route['key_hint']), ('openai', 'gpt-5.4', '9999'))
        # A key is not an allowance: dispatch stays closed until a period exists.
        self.assertFalse(view['dispatch_ready'])
        self.assertFalse(self.call('/api/overview')['provider_dispatch'])
        detail = next(a['detail'] for a in self.call('/api/audit')['audit'] if a['action'] == 'env_update')
        self.assertNotIn('sk-live-9999', detail)

    def test_env_refuses_locked_keys_and_bad_routes(self):
        csrf = self.login()
        self.call('/api/env', {'values': {'DASHBOARD_PASSWORD': 'hunter2'}}, csrf=csrf, status=400)
        self.call('/api/env', {'values': {'RESEARCH_BUDGET_LIMIT_USD': '9999'}}, csrf=csrf, status=400)
        self.call('/api/env', {'values': {'ROLE_REVIEWER': 'notaprovider:x'}}, csrf=csrf, status=400)
        self.call('/api/env', {'values': {'OPENAI_BASE_URL': 'http://evil.example'}}, csrf=csrf, status=400)
        self.assertFalse((self.root / '.env').exists())

    def test_write_without_csrf_rejected(self):
        self.login()
        self.call('/api/messages', {'body': 'no csrf'}, status=403)
