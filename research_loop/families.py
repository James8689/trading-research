"""Minimal opportunity-family registry. Exact IDs and reviewed links only.

No semantic similarity search. Ordinary text fields and foreign keys suffice
until a real research cycle demonstrates a bottleneck that needs more.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
import uuid

from .network import _now


def _text(value, name, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'{name} must be a nonempty string of at most {maximum} characters')
    return value.strip()


class FamilyRegistry:
    def __init__(self, root):
        self.path = Path(root) / 'research_state' / 'families.sqlite3'

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

    def initialize(self):
        with self._db() as db:
            db.execute(
                'CREATE TABLE IF NOT EXISTS families (family_id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, '
                'mechanism_summary TEXT NOT NULL, frozen_plan_hash TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL)'
            )
            db.execute(
                'CREATE TABLE IF NOT EXISTS cycle_links (cycle_id TEXT PRIMARY KEY, family_id TEXT NOT NULL, '
                'linked_at TEXT NOT NULL)'
            )
            db.execute(
                'CREATE TABLE IF NOT EXISTS retrospectives (retro_id TEXT PRIMARY KEY, family_id TEXT NOT NULL, '
                'cycle_id TEXT, bottleneck TEXT NOT NULL, task_ids TEXT, created_at TEXT NOT NULL)'
            )
        return {'path': str(self.path)}

    def register(self, candidate_id, mechanism_summary, frozen_plan_hash=None, status='feasibility_pending'):
        candidate_id = _text(candidate_id, 'candidate_id', 200)
        mechanism_summary = _text(mechanism_summary, 'mechanism_summary', 2000)
        if frozen_plan_hash is not None:
            frozen_plan_hash = _text(frozen_plan_hash, 'frozen_plan_hash', 64)
        status = _text(status, 'status', 80)
        with self._db() as db:
            existing = db.execute('SELECT * FROM families WHERE candidate_id=?', (candidate_id,)).fetchone()
            if existing:
                return dict(existing) | {'duplicate': True}
            family_id = 'family_' + uuid.uuid4().hex
            db.execute(
                'INSERT INTO families VALUES (?,?,?,?,?,?)',
                (family_id, candidate_id, mechanism_summary, frozen_plan_hash, status, _now()),
            )
            return dict(db.execute('SELECT * FROM families WHERE family_id=?', (family_id,)).fetchone())

    def link_cycle(self, family_id, cycle_id):
        family_id = _text(family_id, 'family_id', 80)
        cycle_id = _text(cycle_id, 'cycle_id', 80)
        with self._db() as db:
            if not db.execute('SELECT 1 FROM families WHERE family_id=?', (family_id,)).fetchone():
                raise ValueError('unknown family')
            existing = db.execute('SELECT * FROM cycle_links WHERE cycle_id=?', (cycle_id,)).fetchone()
            if existing:
                return dict(existing) | {'duplicate': True}
            db.execute('INSERT INTO cycle_links VALUES (?,?,?)', (cycle_id, family_id, _now()))
            return dict(db.execute('SELECT * FROM cycle_links WHERE cycle_id=?', (cycle_id,)).fetchone())

    def record_retrospective(self, family_id, bottleneck, cycle_id=None, task_ids=None):
        family_id = _text(family_id, 'family_id', 80)
        bottleneck = _text(bottleneck, 'bottleneck', 4000)
        if cycle_id is not None:
            cycle_id = _text(cycle_id, 'cycle_id', 80)
        encoded = None
        if task_ids is not None:
            if not isinstance(task_ids, list) or any(not isinstance(x, str) or not x or len(x) > 80 for x in task_ids):
                raise ValueError('task_ids must be a list of short strings')
            encoded = ','.join(task_ids)
            if len(encoded) > 4000:
                raise ValueError('task_ids too large')
        with self._db() as db:
            if not db.execute('SELECT 1 FROM families WHERE family_id=?', (family_id,)).fetchone():
                raise ValueError('unknown family')
            retro_id = 'retro_' + uuid.uuid4().hex
            db.execute(
                'INSERT INTO retrospectives VALUES (?,?,?,?,?,?)',
                (retro_id, family_id, cycle_id, bottleneck, encoded, _now()),
            )
            return dict(db.execute('SELECT * FROM retrospectives WHERE retro_id=?', (retro_id,)).fetchone())

    def status(self):
        with self._db() as db:
            families = [dict(r) for r in db.execute('SELECT * FROM families ORDER BY rowid')]
            links = [dict(r) for r in db.execute('SELECT * FROM cycle_links ORDER BY rowid')]
            retrospectives = [dict(r) for r in db.execute('SELECT * FROM retrospectives ORDER BY rowid')]
        return {'families': families, 'cycle_links': links, 'retrospectives': retrospectives}
