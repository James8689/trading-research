"""Offline, deterministic prompt improvement gates.

Costs are arbitrary evaluation units, never money. Synthetic suite labels are
withheld from packets but are NOT technically sealed from local file readers.
Passing fixture tests proves gate behavior, not model or trading quality.
Only role prompts are versioned; controller policy cannot be changed here.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from contextlib import contextmanager
import sqlite3

ROLES = frozenset({'researcher', 'data_auditor', 'reviewer', 'director_plan',
                   'director_decision', 'improvement_proposal'})


def _text(value, name, maximum=100000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'{name} must be a nonempty string of at most {maximum} characters')
    return value


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


class ImprovementRegistry:
    def __init__(self, root):
        self.path = Path(root) / 'research_state' / 'improvement.sqlite3'

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS records(kind TEXT, id TEXT, body TEXT,
                    PRIMARY KEY(kind,id));
                CREATE TABLE IF NOT EXISTS active(role TEXT PRIMARY KEY, version TEXT);
                CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT, previous TEXT, current TEXT, action TEXT, reason TEXT);
                CREATE TABLE IF NOT EXISTS consumed(suite TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS pairings(suite TEXT PRIMARY KEY,
                    candidate TEXT, baseline TEXT, fingerprint TEXT UNIQUE);
            ''')
        return {'path': str(self.path)}

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                db.execute('BEGIN IMMEDIATE')
                yield db
        finally:
            db.close()

    def _get(self, db, kind, identifier):
        _text(identifier, 'id', 64)
        row = db.execute('SELECT body FROM records WHERE kind=? AND id=?', (kind, identifier)).fetchone()
        if row is None:
            raise ValueError(f'Unknown {kind}: {identifier}')
        return json.loads(row[0])

    def _put(self, db, kind, record):
        db.execute('INSERT INTO records VALUES(?,?,?)', (kind, record['id'], _json(record)))
        return record

    def register(self, role, prompt, parent_id=None, rationale='', *, proposer_id=None, provenance=None):
        if not isinstance(role, str) or role not in ROLES:
            raise ValueError('Only permitted role prompts may be registered')
        _text(prompt, 'prompt', 6000)
        if not isinstance(rationale, str) or len(rationale) > 10000:
            raise ValueError('Invalid rationale')
        if proposer_id is not None:
            _text(proposer_id, 'proposer_id', 200)
        if provenance is not None:
            if not isinstance(provenance, (str, dict)):
                raise ValueError('provenance must be a string or object')
            try:
                encoded = _json(provenance)
            except (TypeError, ValueError) as exc:
                raise ValueError('provenance must be finite JSON') from exc
            if len(encoded) > 10000:
                raise ValueError('provenance too large')
        with self._db() as db:
            if parent_id is not None and self._get(db, 'version', parent_id)['role'] != role:
                raise ValueError('Parent must have same role')
            payload = dict(role=role, prompt=prompt, parent_id=parent_id, rationale=rationale,
                           proposer_id=proposer_id, provenance=provenance)
            identifier = _hash(payload)
            existing = db.execute('SELECT body FROM records WHERE kind=? AND id=?', ('version', identifier)).fetchone()
            if existing:
                return json.loads(existing[0])
            return self._put(db, 'version', dict(id=identifier, status='candidate', **payload))

    def build_suite(self, cases):
        if not isinstance(cases, list) or not 1 <= len(cases) <= 10000:
            raise ValueError('Suite requires 1..10000 cases')
        normalized, seen = [], set()
        for case in cases:
            if not isinstance(case, dict) or set(case) != {'id', 'prompt', 'expected_decision', 'critical'}:
                raise ValueError('Invalid case fields')
            for key in ('id', 'prompt', 'expected_decision'):
                _text(case[key], key)
            if type(case['critical']) is not bool or case['id'] in seen:
                raise ValueError('Critical must be boolean and IDs unique')
            seen.add(case['id'])
            normalized.append(dict(case))
        normalized.sort(key=lambda c: c['id'])
        result = dict(id=_hash(normalized), cases=normalized, kind='synthetic_fixture')
        with self._db() as db:
            db.execute('INSERT OR IGNORE INTO records VALUES(?,?,?)', ('suite', result['id'], _json(result)))
        return result

    def packet(self, suite_id):
        with self._db() as db:
            suite = self._get(db, 'suite', suite_id)
        return {'id': suite['id'], 'cases': [{'id': c['id'], 'prompt': c['prompt']} for c in suite['cases']]}

    def begin_comparison(self, candidate_id, baseline_id, suite_id):
        """Freeze a single challenger before either evaluation exposes scores.

        Semantic case content is reserved permanently, including failed trials;
        relabeling case IDs cannot turn reused evidence into a fresh holdout.
        """
        with self._db() as db:
            candidate = self._get(db, 'version', candidate_id)
            baseline = self._get(db, 'version', baseline_id)
            suite = self._get(db, 'suite', suite_id)
            if (candidate['role'] != baseline['role'] or
                    candidate['parent_id'] != baseline_id or
                    candidate['prompt'] == baseline['prompt']):
                raise ValueError('Candidate requires active baseline parent and changed prompt')
            active = db.execute('SELECT version FROM active WHERE role=?', (baseline['role'],)).fetchone()
            if not active or active[0] != baseline_id:
                raise ValueError('Baseline must be active')
            fingerprint = _hash(sorted(
                [_json({key: value for key, value in case.items() if key != 'id'})
                 for case in suite['cases']]))
            if (db.execute('SELECT 1 FROM consumed WHERE suite=?', (suite_id,)).fetchone() or
                    db.execute('SELECT 1 FROM pairings WHERE suite=? OR fingerprint=?',
                               (suite_id, fingerprint)).fetchone()):
                raise ValueError('Suite or semantic case content already reserved')
            # Legacy evaluations cannot retrospectively acquire a comparison.
            for version in (candidate_id, baseline_id):
                if db.execute('SELECT 1 FROM records WHERE kind=? AND id=?',
                              ('evaluation', _hash([version, suite_id]))).fetchone():
                    raise ValueError('Comparison must be frozen before evaluation')
            db.execute('INSERT INTO pairings VALUES(?,?,?,?)',
                       (suite_id, candidate_id, baseline_id, fingerprint))
        return {'id': _hash([candidate_id, baseline_id, suite_id]),
                'candidate_id': candidate_id, 'baseline_id': baseline_id,
                'suite_id': suite_id, 'semantic_fingerprint': fingerprint}

    def bootstrap(self, version_id):
        with self._db() as db:
            version = self._get(db, 'version', version_id)
            role = version['role']
            if db.execute('SELECT 1 FROM history WHERE role=?', (role,)).fetchone():
                raise ValueError('Role already bootstrapped')
            db.execute('INSERT INTO active VALUES(?,?)', (role, version_id))
            db.execute('INSERT INTO history(role,previous,current,action,reason) VALUES(?,?,?,?,?)',
                       (role, None, version_id, 'bootstrap', 'Explicit initial baseline'))
        return {'id': version_id, 'role': role, 'status': 'active'}

    def evaluate(self, version_id, suite_id, answers, cost_units, evaluator_id):
        if type(cost_units) is not int or not 0 <= cost_units <= 10**12:
            raise ValueError('cost_units must be a bounded nonnegative integer')
        _text(evaluator_id, 'evaluator_id', 200)
        if not isinstance(answers, list):
            raise ValueError('answers must be a list')
        mapped = {}
        for answer in answers:
            if not isinstance(answer, dict) or set(answer) != {'case_id', 'decision'}:
                raise ValueError('Invalid answer fields')
            _text(answer['case_id'], 'case_id')
            _text(answer['decision'], 'decision')
            if answer['case_id'] in mapped:
                raise ValueError('Duplicate answer')
            mapped[answer['case_id']] = answer['decision']
        with self._db() as db:
            version = self._get(db, 'version', version_id)
            if version.get('proposer_id') == evaluator_id:
                raise ValueError('Evaluator must be independent of proposer')
            suite = self._get(db, 'suite', suite_id)
            pair = db.execute('SELECT candidate,baseline FROM pairings WHERE suite=?', (suite_id,)).fetchone()
            if not pair or version_id not in pair:
                raise ValueError('Version must belong to a frozen comparison before evaluation')
            if db.execute('SELECT 1 FROM consumed WHERE suite=?', (suite_id,)).fetchone():
                raise ValueError('Suite consumed')
            identifier = _hash([version_id, suite_id])
            if db.execute('SELECT 1 FROM records WHERE kind=? AND id=?', ('evaluation', identifier)).fetchone():
                raise ValueError('Evaluation is immutable; use fresh suite')
            if set(mapped) != {c['id'] for c in suite['cases']}:
                raise ValueError('Exactly one answer for every frozen case is required')
            correct = sum(mapped[c['id']] == c['expected_decision'] for c in suite['cases'])
            misses = sum(c['critical'] and mapped[c['id']] != c['expected_decision'] for c in suite['cases'])
            return self._put(db, 'evaluation', dict(id=identifier, version_id=version_id,
                suite_id=suite_id, accuracy=correct / len(mapped), correct=correct,
                case_count=len(mapped), critical_misses=misses, cost_units=cost_units,
                cost_unit_label='arbitrary evaluation units (not money)', evaluator_id=evaluator_id,
                answers_hash=_hash(mapped), version_hash=version_id, suite_hash=suite_id))

    def promote(self, candidate_id, baseline_id, suite_id, reviewer_id):
        _text(reviewer_id, 'reviewer_id', 200)
        failure = None
        with self._db() as db:
            candidate = self._get(db, 'version', candidate_id)
            baseline = self._get(db, 'version', baseline_id)
            if candidate_id == baseline_id or candidate['role'] != baseline['role']:
                raise ValueError('Distinct versions of the same role required')
            role = candidate['role']
            active = db.execute('SELECT version FROM active WHERE role=?', (role,)).fetchone()
            if not active or active[0] != baseline_id:
                raise ValueError('Baseline must be active')
            pair = db.execute('SELECT candidate,baseline FROM pairings WHERE suite=?', (suite_id,)).fetchone()
            if pair != (candidate_id, baseline_id):
                raise ValueError('Promotion must match frozen comparison')
            if db.execute('SELECT 1 FROM consumed WHERE suite=?', (suite_id,)).fetchone():
                raise ValueError('Suite already used for promotion comparison')
            c = self._get(db, 'evaluation', _hash([candidate_id, suite_id]))
            b = self._get(db, 'evaluation', _hash([baseline_id, suite_id]))
            db.execute('INSERT INTO consumed VALUES(?)', (suite_id,))
            if reviewer_id in {c['evaluator_id'], b['evaluator_id'], candidate.get('proposer_id')}:
                failure = 'Reviewer must be independent of evaluators and proposer'
            elif c['critical_misses'] or c['correct'] < b['correct'] or not (
                    c['correct'] > b['correct'] or c['cost_units'] < b['cost_units']):
                failure = 'Candidate failed accuracy, critical-error, or improvement gate'
            result = dict(id=_hash([candidate_id, baseline_id, suite_id, reviewer_id]),
                          candidate_id=candidate_id, baseline_id=baseline_id, suite_id=suite_id,
                          reviewer_id=reviewer_id, promoted=failure is None, reason=failure or 'Gate passed')
            self._put(db, 'comparison', result)
            if failure is None:
                db.execute('UPDATE active SET version=? WHERE role=?', (candidate_id, role))
                db.execute('INSERT INTO history(role,previous,current,action,reason) VALUES(?,?,?,?,?)',
                           (role, baseline_id, candidate_id, 'promote', result['id']))
        if failure:
            raise ValueError(failure)
        return result

    def rollback(self, role, reason):
        _text(reason, 'reason', 10000)
        if not isinstance(role, str) or role not in ROLES:
            raise ValueError('Unknown role')
        with self._db() as db:
            last = db.execute('SELECT previous,current,action FROM history WHERE role=? ORDER BY seq DESC LIMIT 1', (role,)).fetchone()
            if not last or last[2] != 'promote' or last[0] is None:
                raise ValueError('No promoted version available to roll back')
            db.execute('UPDATE active SET version=? WHERE role=?', (last[0], role))
            db.execute('INSERT INTO history(role,previous,current,action,reason) VALUES(?,?,?,?,?)',
                       (role, last[1], last[0], 'rollback', reason))
            return {'id': last[0], 'role': role, 'status': 'active', 'reason': reason}

    def active(self, role):
        if not isinstance(role, str) or role not in ROLES:
            raise ValueError('Unknown role')
        with self._db() as db:
            row = db.execute('SELECT version FROM active WHERE role=?', (role,)).fetchone()
            if row is None:
                return None
            return dict(self._get(db, 'version', row[0]), status='active')

    def status(self):
        with self._db() as db:
            active = {role: version for role, version in db.execute('SELECT role,version FROM active ORDER BY role')}
            history = [dict(zip(('seq', 'role', 'previous', 'current', 'action', 'reason'), row))
                       for row in db.execute('SELECT seq,role,previous,current,action,reason FROM history ORDER BY seq')]
        return {'active': active, 'history': history}
