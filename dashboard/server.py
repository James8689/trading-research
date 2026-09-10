"""Single-operator dashboard. Stdlib only. Secrets stay in gitignored .env."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json
import os
import sys
import threading
import time

from .service import Dashboard
from .store import UIStore, bootstrap_password
from research_loop.envfile import apply_file_to_os

STATIC = Path(__file__).resolve().parent / 'static'
COOKIE = 'dashboard_session'
MAX_BODY = 120_000
LOGIN_WINDOW = 600
LOGIN_LIMIT = 8
HELP = '''Commands I understand:
/brief — the context I am holding
/status — queue, claims, and spend
/seed-cef — register the CEF cycle and fill the queue
/stop <reason> — hold back new task claims
/resume — admit task claims again
/idea <text> — park an idea without opening a cycle
/claim <worker> [role] — lease the next packet to a worker id
/dispatch [role] — send one leased packet to its mapped model
Free text is saved as a standing instruction. Nothing starts on its own.'''


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


class RateLimit:
    def __init__(self):
        self._hits = {}
        self._lock = threading.Lock()

    def allow(self, key):
        now = time.time()
        with self._lock:
            stamps = [t for t in self._hits.get(key, []) if now - t < LOGIN_WINDOW]
            if len(stamps) >= LOGIN_LIMIT:
                self._hits[key] = stamps
                return False
            stamps.append(now)
            self._hits[key] = stamps
            return True


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = 'OpportunityDashboard/1'

    def log_message(self, format, *args):
        sys.stderr.write('%s - %s\n' % (self.address_string(), format % args))

    def _store(self) -> UIStore:
        return self.server.store

    def _dash(self) -> Dashboard:
        return self.server.dashboard

    def _cookie(self):
        header = self.headers.get('Cookie', '')
        for part in header.split(';'):
            if '=' in part:
                name, value = part.strip().split('=', 1)
                if name == COOKIE:
                    return value
        return None

    def _session(self):
        return self._store().get_session(self._cookie())

    def _set_cookie(self, session_id, max_age):
        flags = f'{COOKIE}={session_id}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}'
        if self.server.secure:
            flags += '; Secure'
        self.send_header('Set-Cookie', flags)

    def _security(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cache-Control', 'no-store')

    def _send(self, code, body, content_type='application/json; charset=utf-8', extra=None):
        payload = body if isinstance(body, bytes) else body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self._security()
        if extra:
            extra()
        self.end_headers()
        self.wfile.write(payload)

    def _error(self, code, message):
        self._send(code, _json({'error': message}))

    def _read_json(self):
        length = int(self.headers.get('Content-Length', '0') or '0')
        if length < 0 or length > MAX_BODY:
            raise ValueError('request body too large')
        raw = self.rfile.read(length) if length else b'{}'
        try:
            data = json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError('invalid JSON') from exc
        if not isinstance(data, dict):
            raise ValueError('JSON object required')
        return data

    def _require(self):
        session = self._session()
        if session is None:
            self._error(401, 'authentication required')
            return None
        return session

    def _require_csrf(self, session):
        token = self.headers.get('X-CSRF-Token', '')
        if not token or token != session['csrf']:
            self._error(403, 'csrf token missing or invalid')
            return False
        return True

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ('/', '/index.html'):
            return self._send(200, (STATIC / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        if path.startswith('/static/'):
            name = path.split('/', 2)[-1]
            target = (STATIC / name).resolve()
            if not str(target).startswith(str(STATIC.resolve())) or not target.is_file():
                return self._error(404, 'not found')
            types = {'.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8'}
            return self._send(200, target.read_bytes(), types.get(target.suffix, 'application/octet-stream'))
        if path == '/api/health':
            return self._send(200, _json({'ok': True, 'mode': 'assisted_manual'}))
        session = self._require()
        if session is None:
            return
        routes = {
            '/api/me': lambda: {'operator': 'james', 'csrf': session['csrf'], 'mode': 'assisted_manual'},
            '/api/overview': self._dash().overview,
            '/api/brief': self._dash().brief,
            '/api/spend': lambda: {**self._dash().spend(), 'accounts': self._store().list_accounts()},
            '/api/env': self._dash().env_view,
            '/api/families': self._dash().families.status,
            '/api/messages': lambda: {'messages': self._store().list_messages(), 'jobs': self._store().list_jobs(), 'ideas': self._store().list_ideas()},
            '/api/ideas': lambda: {'ideas': self._store().list_ideas()},
            '/api/audit': lambda: {'audit': self._store().list_audit(), 'sources': self._dash().network.list_sources()},
            '/api/roles': lambda: {'roles': [self._dash().role(r) for r in self._dash().overview()['roles']]},
        }
        if path in routes:
            try:
                return self._send(200, _json(routes[path]()))
            except (ValueError, RuntimeError, OSError) as exc:
                return self._error(400, str(exc))
        if path.startswith('/api/roles/'):
            name = path.rsplit('/', 1)[-1]
            try:
                return self._send(200, _json(self._dash().role(name)))
            except ValueError as exc:
                return self._error(404, str(exc))
        if path.startswith('/api/tasks/'):
            task_id = path.rsplit('/', 1)[-1]
            try:
                return self._send(200, _json(self._dash().task(task_id)))
            except ValueError as exc:
                return self._error(404, str(exc))
        return self._error(404, 'not found')

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == '/api/login':
            return self._login()
        session = self._require()
        if session is None:
            return
        if path == '/api/logout':
            self._store().drop_session(session['session_id'])
            self._store().audit('james', 'logout', '')
            return self._send(200, _json({'ok': True}), extra=lambda: self._set_cookie('deleted', 0))
        if not self._require_csrf(session):
            return
        try:
            body = self._read_json()
        except ValueError as exc:
            return self._error(400, str(exc))
        try:
            if path == '/api/messages':
                return self._send(200, _json(self._handle_message(body)))
            if path == '/api/ideas':
                idea = self._store().add_idea(body.get('body', ''))
                self._store().audit('james', 'idea', idea['idea_id'])
                return self._send(200, _json(idea))
            if path == '/api/env':
                value = self._dash().save_env(body.get('values') or {})
                # Log variable names and whether they were set. Never the value.
                self._store().audit('james', 'env_update', json.dumps(
                    [{'key': s['key'], 'set': s['set']} for s in value['saved']]))
                return self._send(200, _json(value))
            if path == '/api/accounts':
                account = self._store().upsert_account(
                    body.get('alias', ''), body.get('provider', ''),
                    body.get('model'), body.get('key_hint'), body.get('notes'),
                )
                self._store().audit('james', 'account_upsert', account['alias'])
                return self._send(200, _json(account))
            if path == '/api/control/seed-cef':
                value = self._dash().seed_cef(body.get('evidence') or [])
                self._store().audit('james', 'seed_cef', value.get('cycle_id', ''))
                return self._send(200, _json(value))
            if path == '/api/control/ingest':
                value = self._dash().ingest(body.get('source_id', ''), body.get('content', ''), body.get('published_at'))
                self._store().audit('james', 'ingest', value.get('event_id', ''))
                return self._send(200, _json(value))
            if path == '/api/control/claim':
                value = self._dash().claim(body.get('worker_id', ''), body.get('role'))
                self._store().audit('james', 'claim', json.dumps({'worker': body.get('worker_id'), 'role': body.get('role')}))
                return self._send(200, _json(value))
            if path == '/api/control/submit':
                value = self._dash().submit(body.get('task_id', ''), body.get('worker_id', ''), body.get('result'))
                self._store().audit('james', 'submit', body.get('task_id', ''))
                return self._send(200, _json(value))
            if path == '/api/control/fail':
                value = self._dash().fail(body.get('task_id', ''), body.get('worker_id', ''), body.get('reason', ''))
                self._store().audit('james', 'fail', body.get('task_id', ''))
                return self._send(200, _json(value))
            if path == '/api/control/stop':
                value = self._dash().stop(body.get('reason', ''))
                self._store().audit('james', 'stop', body.get('reason', ''))
                return self._send(200, _json(value))
            if path == '/api/control/resume':
                value = self._dash().resume()
                self._store().audit('james', 'resume', '')
                return self._send(200, _json(value))
            if path == '/api/control/dispatch':
                value = self._dash().dispatch(body.get('role') or None)
                self._store().audit('james', 'dispatch', json.dumps({'role': body.get('role'), 'task': value.get('task_id'), 'model': value.get('model')}))
                return self._send(200, _json({k: v for k, v in value.items() if k != 'result'} | {'decision': (value.get('result') or {}).get('decision')}))
            if path == '/api/families/retrospective':
                value = self._dash().families.record_retrospective(
                    body.get('family_id', ''), body.get('bottleneck', ''),
                    body.get('cycle_id'), body.get('task_ids'),
                )
                self._store().audit('james', 'retrospective', value.get('retro_id', ''))
                return self._send(200, _json(value))
        except (ValueError, RuntimeError, TypeError, OSError) as exc:
            return self._error(400, str(exc))
        return self._error(404, 'not found')

    def _login(self):
        if not self.server.limiter.allow(self.client_address[0]):
            return self._error(429, 'too many login attempts')
        try:
            body = self._read_json()
        except ValueError as exc:
            return self._error(400, str(exc))
        password = body.get('password', '')
        if not self._store().verify_password(password):
            self._store().audit('anonymous', 'login_failed', self.client_address[0])
            return self._error(401, 'invalid password')
        session = self._store().create_session()
        self._store().audit('james', 'login', '')
        return self._send(
            200,
            _json({'ok': True, 'csrf': session['csrf'], 'operator': 'james'}),
            extra=lambda: self._set_cookie(session['session_id'], session['expires_at'] - int(time.time())),
        )

    def _handle_message(self, body):
        text = body.get('body', '')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('message body required')
        brief = self._dash().brief()
        stored = self._store().add_message('james', text.strip(), brief)
        job = self._store().add_job('director_instruction', {'body': text.strip()})
        reply, result, status, error = self._dispatch_instruction(text.strip(), brief)
        self._store().finish_job(job['job_id'], status, result, error)
        director = self._store().add_message('director', reply, brief, job['job_id'])
        self._store().audit('james', 'orchestrator_message', stored['message_id'])
        return {'message': stored, 'reply': director, 'job': job | {'status': status, 'error': error}, 'brief': brief}

    def _dispatch_instruction(self, text, brief):
        """Plain-language replies. Mutating commands also append to the log."""
        counts = brief.get('task_counts') or {}
        pending, leased = counts.get('pending', 0), counts.get('leased', 0)
        queued = brief.get('pending_and_leased') or []
        next_id = queued[0]['task_id'] if queued else 'none'
        if not text.startswith('/'):
            reply = (
                'Saved as a standing instruction. I will fold it into the next plan I write. '
                'Nothing has started.\n'
                f'Waiting {pending} · working {leased} · next {next_id}.'
            )
            return reply, {'recorded': True}, 'queued', None
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ''
        try:
            if command == '/help':
                return (HELP, {'ok': True}, 'completed', None)
            if command == '/brief':
                reply = (
                    f"Owner: {brief.get('context_owner')}\n"
                    f"Objective: {brief.get('objective')}\n"
                    f'Waiting {pending} · working {leased} · next {next_id}'
                )
                return reply, brief, 'completed', None
            if command == '/status':
                return self._status_reply()
            if command == '/seed-cef':
                value = self._dash().seed_cef()
                self._store().audit('james', 'command', '/seed-cef')
                if value.get('duplicate'):
                    return (
                        'A cycle is already registered against the frozen B3 plan. '
                        'Seeding again is refused.', value, 'completed', None,
                    )
                return (
                    'Seeded the CEF document-feasibility cycle. B3-H1-v1 is registered against '
                    'the frozen B3 plan and the queue is filled. No model was called.',
                    value, 'completed', None,
                )
            if command == '/stop':
                if not arg:
                    raise ValueError('usage: /stop <reason>. The reason is stored with the stop.')
                value = self._dash().stop(arg)
                self._store().audit('james', 'command', '/stop')
                return (
                    'New task claims stopped. Open leases and the ledger are untouched — nothing is wiped.',
                    value, 'completed', None,
                )
            if command == '/resume':
                value = self._dash().resume()
                self._store().audit('james', 'command', '/resume')
                return ('Task claims admitted again. Existing leases were never dropped.', value, 'completed', None)
            if command == '/idea':
                if not arg:
                    raise ValueError('usage: /idea <text>')
                value = self._store().add_idea(arg)
                self._store().audit('james', 'idea', value['idea_id'])
                return ('Saved to the idea inbox. No cycle opens.', value, 'completed', None)
            if command == '/claim':
                return self._claim_reply(arg)
            if command == '/dispatch':
                return self._dispatch_reply(arg)
            return (f'I do not know {command}. Try /help.', None, 'completed', None)
        except (ValueError, RuntimeError) as exc:
            return f'That did not work: {exc}', None, 'failed', str(exc)

    def _status_reply(self):
        overview = self._dash().overview()
        counts = overview['task_counts']
        budget = overview['budget']
        done = counts.get('completed', 0)
        stuck = counts.get('failed', 0) + counts.get('blocked', 0)
        spend = (
            f"Spending blocked at ${budget['spent_microusd'] / 1e6:.2f}, so no paid step can run."
            if budget['blocked'] else
            f"Spending open: ${budget['spent_microusd'] / 1e6:.2f} of ${budget['limit_microusd'] / 1e6:.2f} used."
        )
        reply = (
            f"Waiting {counts.get('pending', 0)} · working {counts.get('leased', 0)} · "
            f'done {done} · failed or blocked {stuck}\n'
            f"Task claims {'stopped' if overview['policy']['stopped'] else 'admitted'}. {spend}\n"
            f"Frozen plan {'verified' if overview['freeze']['ok'] else 'does NOT match its receipt'}."
        )
        return reply, {'task_counts': counts, 'blocked': budget['blocked']}, 'completed', None

    def _claim_reply(self, arg):
        bits = arg.split()
        if not bits:
            raise ValueError('usage: /claim <worker-id> [role]')
        worker, role = bits[0], bits[1] if len(bits) > 1 else None
        value = self._dash().claim(worker, role)
        self._store().audit('james', 'claim', json.dumps({'worker': worker, 'role': role}))
        if not value.get('claimed'):
            return (f"Nothing claimable for {worker}: {value.get('reason')}", value, 'completed', None)
        packet = value['packet']
        return (
            f"Leased {packet['task_id']} ({packet['role']}) to {worker}. The packet is frozen; "
            'submit or fail it to release the lease.',
            value, 'completed', None,
        )

    def _dispatch_reply(self, arg):
        value = self._dash().dispatch(arg.strip() or None)
        self._store().audit('james', 'dispatch', json.dumps(
            {'role': value.get('role'), 'task': value.get('task_id'), 'model': value.get('model')}))
        usage = value.get('usage') or {}
        decision = (value.get('result') or {}).get('decision')
        reply = (
            f"Sent one {value['role']} packet to {value['provider']}:{value['model']}.\n"
            f"Decision: {decision}. Task {value['task_id']}.\n"
            f"Tokens in/out: {usage.get('prompt_tokens', '?')}/{usage.get('completion_tokens', '?')}."
        )
        return reply, value, 'completed', None


def make_server(root, host='127.0.0.1', port=8787, password=None, secure=False):
    root = Path(root).resolve()
    apply_file_to_os(root)
    store = UIStore(root)
    generated = None
    if password:
        store.set_password(password)
    else:
        generated = bootstrap_password(store)
    dashboard = Dashboard(root)
    httpd = ThreadingHTTPServer((host, port), DashboardHandler)
    httpd.store = store
    httpd.dashboard = dashboard
    httpd.limiter = RateLimit()
    httpd.secure = secure
    httpd.generated_password = generated
    return httpd


def serve(root, host=None, port=None, password=None):
    host = host or os.environ.get('DASHBOARD_HOST', '0.0.0.0')
    port = int(port or os.environ.get('DASHBOARD_PORT', '8787'))
    secure = os.environ.get('DASHBOARD_SECURE', '').lower() in {'1', 'true', 'yes'}
    httpd = make_server(root, host, port, password, secure)
    bound = httpd.server_address
    print(f'Dashboard listening on http://{bound[0]}:{bound[1]}', flush=True)
    print('Single-operator access. Persistence is research_state/*.sqlite3 (gitignored).', flush=True)
    print('No broker. Model dispatch uses gitignored .env keys and a fail-closed ledger.', flush=True)
    overview = httpd.dashboard.overview()
    if overview['provider_dispatch']:
        print('Provider dispatch is available. /dispatch sends one packet per request.', flush=True)
    else:
        print('Provider dispatch is idle until .env has keys and a budget period.', flush=True)
    if httpd.generated_password:
        print(f'Generated login password (shown once): {httpd.generated_password}', flush=True)
    elif os.environ.get('DASHBOARD_PASSWORD'):
        print('Login password taken from DASHBOARD_PASSWORD.', flush=True)
    else:
        print('Using the password already stored in research_state/ui.sqlite3.', flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Dashboard stopped.', flush=True)
    finally:
        httpd.server_close()
    return 0
