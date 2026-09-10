"""Durable operator UI state. Not a research-evidence store.

Sessions, orchestrator messages, ideas, jobs and the audit log live here so a
restart or cloud remount of research_state/ continues the same console.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time

from research_loop.network import _now


SESSION_SECONDS = 30 * 24 * 3600
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def _text(value, name, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'{name} must be a nonempty string of at most {maximum} characters')
    return value.strip()


class UIStore:
    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / 'research_state' / 'ui.sqlite3'
        self._ensure()

    @contextmanager
    def _db(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _ensure(self):
        with self._db() as db:
            db.executescript(
                '''
                CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY, csrf TEXT NOT NULL, created_at TEXT NOT NULL,
                    expires_at INTEGER NOT NULL, last_seen INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, author TEXT NOT NULL,
                    body TEXT NOT NULL, brief_json TEXT, job_id TEXT
                );
                CREATE TABLE IF NOT EXISTS ideas (
                    idea_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, body TEXT NOT NULL,
                    status TEXT NOT NULL, notes TEXT
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, kind TEXT NOT NULL,
                    payload TEXT NOT NULL, status TEXT NOT NULL, result TEXT, error TEXT
                );
                CREATE TABLE IF NOT EXISTS accounts (
                    alias TEXT PRIMARY KEY, provider TEXT NOT NULL, model TEXT,
                    key_hint TEXT, notes TEXT, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit (
                    audit_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, actor TEXT NOT NULL,
                    action TEXT NOT NULL, detail TEXT NOT NULL
                );
                '''
            )

    def set_password(self, password):
        password = _text(password, 'password', 200)
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32)
        stored = salt.hex() + '$' + digest.hex()
        with self._db() as db:
            db.execute("INSERT OR REPLACE INTO meta VALUES ('password_hash', ?)", (stored,))
        return {'set': True}

    def has_password(self):
        with self._db() as db:
            row = db.execute("SELECT v FROM meta WHERE k='password_hash'").fetchone()
        return row is not None

    def verify_password(self, password):
        if not isinstance(password, str) or not password:
            return False
        with self._db() as db:
            row = db.execute("SELECT v FROM meta WHERE k='password_hash'").fetchone()
        if row is None:
            return False
        salt_hex, digest_hex = row['v'].split('$', 1)
        candidate = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex), n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)

    def create_session(self):
        session_id = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(24)
        now = int(time.time())
        with self._db() as db:
            db.execute(
                'INSERT INTO sessions VALUES (?,?,?,?,?)',
                (session_id, csrf, _now(), now + SESSION_SECONDS, now),
            )
        return {'session_id': session_id, 'csrf': csrf, 'expires_at': now + SESSION_SECONDS}

    def get_session(self, session_id):
        if not isinstance(session_id, str) or not session_id:
            return None
        now = int(time.time())
        with self._db() as db:
            row = db.execute('SELECT * FROM sessions WHERE session_id=?', (session_id,)).fetchone()
            if row is None or row['expires_at'] < now:
                if row is not None:
                    db.execute('DELETE FROM sessions WHERE session_id=?', (session_id,))
                return None
            db.execute('UPDATE sessions SET last_seen=? WHERE session_id=?', (now, session_id))
            return dict(row)

    def drop_session(self, session_id):
        with self._db() as db:
            db.execute('DELETE FROM sessions WHERE session_id=?', (session_id,))

    def add_message(self, author, body, brief=None, job_id=None):
        author = _text(author, 'author', 40)
        if author not in ('james', 'director', 'system'):
            raise ValueError('unknown message author')
        body = _text(body, 'body', 8000)
        encoded = json.dumps(brief, sort_keys=True, ensure_ascii=False) if brief is not None else None
        if encoded is not None and len(encoded) > 20000:
            encoded = encoded[:20000]
        message_id = 'msg_' + secrets.token_hex(12)
        with self._db() as db:
            db.execute(
                'INSERT INTO messages VALUES (?,?,?,?,?,?)',
                (message_id, _now(), author, body, encoded, job_id),
            )
            return dict(db.execute('SELECT message_id, created_at, author, body, job_id FROM messages WHERE message_id=?', (message_id,)).fetchone())

    def list_messages(self, limit=200):
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError('limit out of range')
        with self._db() as db:
            rows = db.execute(
                'SELECT message_id, created_at, author, body, job_id FROM messages ORDER BY rowid DESC LIMIT ?',
                (limit,),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def add_idea(self, body):
        body = _text(body, 'body', 4000)
        idea_id = 'idea_' + secrets.token_hex(12)
        with self._db() as db:
            db.execute('INSERT INTO ideas VALUES (?,?,?,?,?)', (idea_id, _now(), body, 'inbox', None))
            return dict(db.execute('SELECT * FROM ideas WHERE idea_id=?', (idea_id,)).fetchone())

    def list_ideas(self):
        with self._db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM ideas ORDER BY rowid DESC')]

    def add_job(self, kind, payload, status='queued'):
        kind = _text(kind, 'kind', 80)
        status = _text(status, 'status', 40)
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        if len(encoded) > 20000:
            raise ValueError('job payload too large')
        job_id = 'job_' + secrets.token_hex(12)
        with self._db() as db:
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?)', (job_id, _now(), kind, encoded, status, None, None))
            return dict(db.execute('SELECT job_id, created_at, kind, status, error FROM jobs WHERE job_id=?', (job_id,)).fetchone())

    def finish_job(self, job_id, status, result=None, error=None):
        with self._db() as db:
            db.execute(
                'UPDATE jobs SET status=?, result=?, error=? WHERE job_id=?',
                (status, json.dumps(result, ensure_ascii=False) if result is not None else None, error, job_id),
            )
            row = db.execute('SELECT job_id, created_at, kind, status, error FROM jobs WHERE job_id=?', (job_id,)).fetchone()
            if row is None:
                raise ValueError('unknown job')
            return dict(row)

    def list_jobs(self, limit=100):
        with self._db() as db:
            return [dict(r) for r in db.execute(
                'SELECT job_id, created_at, kind, status, error FROM jobs ORDER BY rowid DESC LIMIT ?',
                (limit,),
            )]

    def upsert_account(self, alias, provider, model=None, key_hint=None, notes=None):
        alias = _text(alias, 'alias', 80)
        provider = _text(provider, 'provider', 80)
        if model is not None:
            model = _text(model, 'model', 120)
        if key_hint is not None:
            key_hint = _text(key_hint, 'key_hint', 16)
        if notes is not None:
            notes = _text(notes, 'notes', 500)
        with self._db() as db:
            db.execute(
                'INSERT INTO accounts VALUES (?,?,?,?,?,?) ON CONFLICT(alias) DO UPDATE SET provider=excluded.provider, model=excluded.model, key_hint=excluded.key_hint, notes=excluded.notes',
                (alias, provider, model, key_hint, notes, _now()),
            )
            return dict(db.execute('SELECT * FROM accounts WHERE alias=?', (alias,)).fetchone())

    def list_accounts(self):
        with self._db() as db:
            return [dict(r) for r in db.execute('SELECT alias, provider, model, key_hint, notes, created_at FROM accounts ORDER BY alias')]

    def audit(self, actor, action, detail):
        actor = _text(actor, 'actor', 80)
        action = _text(action, 'action', 80)
        if not isinstance(detail, str):
            detail = json.dumps(detail, ensure_ascii=False)
        if len(detail) > 4000:
            detail = detail[:4000]
        audit_id = 'audit_' + secrets.token_hex(12)
        with self._db() as db:
            db.execute('INSERT INTO audit VALUES (?,?,?,?,?)', (audit_id, _now(), actor, action, detail))
            return audit_id

    def list_audit(self, limit=200):
        with self._db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM audit ORDER BY rowid DESC LIMIT ?', (limit,))]


def bootstrap_password(store, env=None):
    """Use DASHBOARD_PASSWORD when set; otherwise generate once and return it."""
    env = os.environ if env is None else env
    supplied = env.get('DASHBOARD_PASSWORD')
    if supplied:
        if not store.has_password() or not store.verify_password(supplied):
            store.set_password(supplied)
        return None
    if store.has_password():
        return None
    generated = secrets.token_urlsafe(18)
    store.set_password(generated)
    return generated
