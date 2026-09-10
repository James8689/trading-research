"""Durable manual research network; no provider calls or broker capabilities.

SQLite admission is a correctness boundary, not a security boundary against a
same-user process capable of editing the database or this module.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
import sqlite3
import uuid

ROLES = ('director_plan', 'researcher', 'data_auditor', 'reviewer', 'director_decision', 'improvement_proposal')
DECISIONS = {'continue', 'reject', 'blocked', 'inconclusive', 'review_required', 'propose_improvement'}
FIELDS = {'summary', 'decision', 'evidence', 'uncertainty', 'next_action', 'memory'}


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class Network:
    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / 'research_state' / 'network.sqlite3'

    @contextlib.contextmanager
    def _db(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def initialize(self, max_tasks=12, max_concurrent=3):
        if type(max_tasks) is not int or type(max_concurrent) is not int or min(max_tasks, max_concurrent) < 1:
            raise ValueError('caps must be positive integers')
        with self._db() as db:
            statements = [
                'CREATE TABLE IF NOT EXISTS policy (id INTEGER PRIMARY KEY CHECK(id=1), max_tasks INTEGER, max_concurrent INTEGER, stopped INTEGER, reason TEXT)',
                'CREATE TABLE IF NOT EXISTS sources (event_id TEXT PRIMARY KEY, source_id TEXT, content TEXT, content_hash TEXT, published_at TEXT, received_at TEXT, revision INTEGER, UNIQUE(source_id, content_hash, published_at))',
                'CREATE TABLE IF NOT EXISTS cycles (cycle_id TEXT PRIMARY KEY, candidate_id TEXT, question TEXT, evidence_ids TEXT, plan_hash TEXT, created_at TEXT)',
                'CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, cycle_id TEXT REFERENCES cycles, role TEXT, state TEXT, worker_id TEXT, packet TEXT, packet_hash TEXT, result TEXT, reason TEXT, result_hash TEXT, UNIQUE(cycle_id, role))',
                'CREATE TABLE IF NOT EXISTS attempts (attempt_id TEXT PRIMARY KEY, task_id TEXT REFERENCES tasks, worker_id TEXT, started_at TEXT, ended_at TEXT, outcome TEXT, reason TEXT)',
                'CREATE TABLE IF NOT EXISTS memory_history (candidate_id TEXT, role TEXT, version INTEGER, memory TEXT, memory_hash TEXT, task_id TEXT REFERENCES tasks, updated_at TEXT, PRIMARY KEY(candidate_id,role,version))',
                'CREATE TABLE IF NOT EXISTS memory_current (candidate_id TEXT, role TEXT, version INTEGER, PRIMARY KEY(candidate_id,role), FOREIGN KEY(candidate_id,role,version) REFERENCES memory_history(candidate_id,role,version))',
                'CREATE TABLE IF NOT EXISTS submission_errors (error_id TEXT PRIMARY KEY, task_id TEXT REFERENCES tasks, worker_id TEXT, code TEXT, payload_hash TEXT, created_at TEXT)',
                'CREATE TABLE IF NOT EXISTS decisions (task_id TEXT PRIMARY KEY REFERENCES tasks, decision TEXT, created_at TEXT)',
            ]
            for statement in statements:
                db.execute(statement)
            existing = db.execute('SELECT * FROM policy WHERE id=1').fetchone()
            if existing and (existing['max_tasks'] != max_tasks or existing['max_concurrent'] != max_concurrent):
                raise ValueError('persisted caps cannot be changed by initialize')
            db.execute('INSERT OR IGNORE INTO policy VALUES (1,?,?,0,?)', (max_tasks, max_concurrent, ''))
        return self.status()

    def ingest(self, source_id, content, published_at=None):
        if not isinstance(source_id, str) or not source_id.strip() or len(source_id) > 1000:
            raise ValueError('source_id must be nonempty and <=1000 characters')
        if not isinstance(content, str) or not content or len(content) > 16000:
            raise ValueError('content must be nonempty and <=16000 characters; split large documents explicitly')
        if published_at is not None:
            if not isinstance(published_at, str):
                raise ValueError('published_at must be an ISO timestamp')
            stamp = dt.datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                raise ValueError('published_at requires a timezone')
            published_at = stamp.astimezone(dt.timezone.utc).isoformat()
        with self._db() as db:
            row = db.execute('SELECT * FROM sources WHERE source_id=? AND content_hash=? AND published_at IS ?', (source_id, _hash(content), published_at)).fetchone()
            if row:
                return dict(row, duplicate=True)
            revision = db.execute('SELECT COALESCE(MAX(revision),0)+1 FROM sources WHERE source_id=?', (source_id,)).fetchone()[0]
            event_id = 'source_' + uuid.uuid4().hex
            db.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?)', (event_id, source_id, content, _hash(content), published_at, _now(), revision))
            return dict(db.execute('SELECT * FROM sources WHERE event_id=?', (event_id,)).fetchone(), duplicate=False)

    def create_cycle(self, candidate_id, question, evidence_ids, plan_hash):
        for name, value, cap in [('candidate_id', candidate_id, 200), ('question', question, 2000), ('plan_hash', plan_hash, 200)]:
            if not isinstance(value, str) or not value.strip() or len(value) > cap:
                raise ValueError(f'invalid {name}')
        if not re.fullmatch(r'[0-9a-fA-F]{64}', plan_hash):
            raise ValueError('plan_hash requires 64 hex characters')
        if not isinstance(evidence_ids, list) or any(not isinstance(x, str) for x in evidence_ids) or len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError('evidence_ids must be a unique list of source event IDs')
        with self._db() as db:
            for event_id in evidence_ids:
                if not db.execute('SELECT 1 FROM sources WHERE event_id=?', (event_id,)).fetchone():
                    raise ValueError('unknown source event: ' + event_id)
            existing = db.execute('SELECT cycle_id FROM cycles WHERE candidate_id=? AND question=? AND evidence_ids=? AND plan_hash=?', (candidate_id, question, _json(evidence_ids), plan_hash)).fetchone()
            if existing:
                return {'cycle_id': existing[0], 'tasks': {r['role']: r['task_id'] for r in db.execute('SELECT role,task_id FROM tasks WHERE cycle_id=?', (existing[0],))}, 'duplicate': True}
            cycle_id = 'cycle_' + uuid.uuid4().hex
            db.execute('INSERT INTO cycles VALUES (?,?,?,?,?,?)', (cycle_id, candidate_id, question, _json(evidence_ids), plan_hash, _now()))
            tasks = {}
            for role in ROLES:
                task_id = 'task_' + uuid.uuid4().hex
                tasks[role] = task_id
                db.execute('INSERT INTO tasks VALUES (?,?,?,?,NULL,NULL,NULL,NULL,NULL,NULL)', (task_id, cycle_id, role, 'pending'))
            for task_id in tasks.values():
                preview = self._packet(db, db.execute('SELECT * FROM tasks WHERE task_id=?', (task_id,)).fetchone(), 'x' * 200)
                preview['memory'] = ''
                preview['dependencies'] = []
                # Reserve worst-case admitted prompt plus downstream excerpts.
                preview['prompt'] = 'x' * 6000
                preview['prompt_version'] = 'x' * 64
                if len(_json(preview)) > 14500:
                    raise ValueError('cycle source/context exceeds reserved downstream packet capacity; split the cycle')
            return {'cycle_id': cycle_id, 'tasks': tasks}

    def _dependencies(self, role):
        return {'director_plan': [], 'researcher': ['director_plan'], 'data_auditor': ['director_plan'], 'reviewer': ['researcher', 'data_auditor'], 'director_decision': ['researcher', 'data_auditor', 'reviewer'], 'improvement_proposal': ['director_decision']}[role]

    def _packet(self, db, task, worker_id):
        cycle = dict(db.execute('SELECT * FROM cycles WHERE cycle_id=?', (task['cycle_id'],)).fetchone())
        sources = [dict(db.execute('SELECT * FROM sources WHERE event_id=?', (i,)).fetchone()) for i in json.loads(cycle.pop('evidence_ids'))]
        deps = []
        for role in (ROLES[:-1] if task['role'] == 'improvement_proposal' else self._dependencies(task['role'])):
            row = db.execute('SELECT task_id, role, result, result_hash FROM tasks WHERE cycle_id=? AND role=?', (task['cycle_id'], role)).fetchone()
            # Reviewer receives original sources and evidence references, not other agents' interpretations.
            if row and row['result']:
                full = json.loads(row['result'])
                citations = [{'source_id': e['source_id'], 'quote': e['quote'][:100]} for e in full['evidence'][:3]]
                result = {'evidence': citations}
                excerpts = {'evidence_omitted': max(0, len(full['evidence']) - 3),
                            'quote_excerpts': any(len(e['quote']) > 100 for e in full['evidence'][:3])}
                if task['role'] != 'reviewer':
                    result['decision'] = full['decision']
                    for field, cap in [('summary', 300), ('uncertainty', 150), ('next_action', 150)]:
                        result[field] = full[field][:cap]
                        excerpts[field + '_truncated'] = len(full[field]) > cap
                deps.append({'role': role, 'task_id': row['task_id'], 'result_hash': row['result_hash'],
                             'result': result, 'excerpts': excerpts,
                             'full_result_ref': row['task_id']})
        memory = None
        if task['role'] != 'reviewer':
            memory = db.execute('SELECT h.* FROM memory_history h JOIN memory_current c USING(candidate_id,role,version) WHERE h.candidate_id=? AND h.role=?', (cycle['candidate_id'], task['role'])).fetchone()
        packet = {'task_id': task['task_id'], 'worker_id': worker_id, 'role': task['role'], 'cycle': cycle, 'sources': sources, 'dependencies': deps, 'memory': memory['memory'] if memory else '', 'memory_provenance': {k: memory[k] for k in ('candidate_id', 'role', 'version', 'memory_hash', 'task_id')} if memory else None, 'constraints': ['Research only. No broker or provider execution.', 'Return exact result schema. Quote original source text.', 'Do not change frozen plans or controller policy.', 'Improvement proposals require separate held-out evaluation before adoption.', 'Continue means ready for human feasibility review; it does not establish scientific validation.']}
        prompt_path = self.root / 'agents' / 'network' / (task['role'] + '.md')
        defaults = {'director_plan': 'Define a bounded document feasibility task and explicit evidence requirements without altering the frozen plan.', 'researcher': 'Extract source evidence addressing the question, separating observations from interpretation.', 'data_auditor': 'Independently audit document availability, timestamps, contractual terms and missing data.', 'reviewer': 'Independently falsify the evidence using original sources. Identify unsupported assertions and contradictions.', 'director_decision': 'Synthesize the research, audit and review. Continue means ready for human feasibility review, never scientific validation.', 'improvement_proposal': 'Propose a versioned prompt or tool improvement from errors, with held-out evaluation criteria. Do not adopt your own proposal.'}
        prompt = prompt_path.read_text(encoding='utf-8') if prompt_path.exists() else defaults[task['role']]
        if (self.root / 'research_state' / 'improvement.sqlite3').exists():
            from .improvement import ImprovementRegistry
            active = ImprovementRegistry(self.root).active(task['role'])
            if active:
                prompt = active['prompt']
                packet['prompt_version'] = active['id']
        if len(prompt) > 6000:
            raise ValueError('role prompt exceeds 6000 characters; rules cannot be truncated')
        packet['prompt'] = prompt
        packet['prompt_hash'] = _hash(prompt)
        packet['result_schema'] = {'required_fields': sorted(FIELDS), 'decisions': sorted(DECISIONS), 'evidence': [{'source_id': 'source event_id from this packet', 'quote': 'exact nonempty substring of source content'}]}
        packet['memory_truncated'] = False
        # Only interpretive context may be excerpted; sources and rules stay exact.
        if len(_json(packet)) > 19900 and packet['memory']:
            packet['memory'] = packet['memory'][:500]
            packet['memory_truncated'] = len(memory['memory']) > 500
        if len(_json(packet)) > 19900:
            for dep in deps:
                dep['result'] = {'evidence': []} if task['role'] == 'reviewer' else {'decision': dep['result']['decision']}
                dep['excerpts']['details_omitted_for_packet_limit'] = True
        encoded = _json(packet)
        if len(encoded) > 19900:
            raise ValueError('packet exceeds 20000 characters; create a smaller bounded cycle')
        packet['packet_hash'] = _hash(encoded)
        return packet

    def claim(self, worker_id, role=None):
        if not isinstance(worker_id, str) or not worker_id.strip() or len(worker_id) > 200:
            raise ValueError('worker_id must be nonempty and <=200 characters')
        if role is not None and role not in ROLES:
            raise ValueError('unknown role')
        with self._db() as db:
            policy = db.execute('SELECT * FROM policy WHERE id=1').fetchone()
            if policy['stopped'] or db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0] >= policy['max_tasks'] or db.execute("SELECT COUNT(*) FROM tasks WHERE state='leased'").fetchone()[0] >= policy['max_concurrent']:
                return None
            for task in db.execute("SELECT * FROM tasks WHERE state='pending' ORDER BY rowid").fetchall():
                if role and task['role'] != role:
                    continue
                related = {r['role']: r for r in db.execute('SELECT * FROM tasks WHERE cycle_id=?', (task['cycle_id'],))}
                deps = [related[r] for r in self._dependencies(task['role'])]
                if any(r['state'] in ('failed', 'blocked') for r in deps):
                    db.execute("UPDATE tasks SET state='blocked', reason=? WHERE task_id=?", ('dependency failed; no automatic retry', task['task_id']))
                    continue
                if any(r['state'] != 'completed' for r in deps):
                    continue
                if task['role'] == 'improvement_proposal' and related['director_decision']['worker_id'] != worker_id:
                    continue
                forbidden = []
                if task['role'] in ('researcher', 'data_auditor'):
                    forbidden = ['data_auditor' if task['role'] == 'researcher' else 'researcher']
                elif task['role'] == 'reviewer':
                    forbidden = ['researcher', 'data_auditor']
                elif task['role'] == 'director_decision':
                    forbidden = ['researcher', 'data_auditor', 'reviewer']
                if any(related[r]['worker_id'] == worker_id for r in forbidden):
                    continue
                packet = self._packet(db, task, worker_id)
                db.execute("UPDATE tasks SET state='leased', worker_id=?, packet=?, packet_hash=? WHERE task_id=?", (worker_id, _json(packet), packet['packet_hash'], task['task_id']))
                db.execute('INSERT INTO attempts VALUES (?,?,?,?,NULL,NULL,NULL)', ('attempt_' + uuid.uuid4().hex, task['task_id'], worker_id, _now()))
                return packet
            return None

    def _leased(self, db, task_id, worker_id=None):
        task = db.execute('SELECT * FROM tasks WHERE task_id=?', (task_id,)).fetchone()
        if not task or task['state'] != 'leased' or (worker_id is not None and task['worker_id'] != worker_id):
            raise ValueError('task is not leased to this worker')
        return task

    def submit(self, task_id, worker_id, result):
        """Reject invalid results without losing the lease or failure lineage."""
        try:
            return self._submit(task_id, worker_id, result)
        except ValueError as error:
            # Hash only: malformed output may contain sensitive or very large text.
            # The error code is generated here, never copied from worker content.
            try:
                payload_hash = _hash(_json(result))
            except (TypeError, ValueError, RecursionError):
                payload_hash = _hash(type(result).__name__)
            code = 'evidence_rejected' if str(error).startswith(('evidence must', 'this decision requires')) else 'result_rejected'
            with self._db() as db:
                owned = db.execute("SELECT 1 FROM tasks WHERE task_id=? AND worker_id=? AND state='leased'", (task_id, worker_id)).fetchone()
                if owned:
                    db.execute('INSERT INTO submission_errors VALUES (?,?,?,?,?,?)', ('error_' + uuid.uuid4().hex, task_id, worker_id, code, payload_hash, _now()))
            raise

    def _submit(self, task_id, worker_id, result):
        if not isinstance(result, dict) or set(result) != FIELDS:
            raise ValueError('result requires exactly: ' + ', '.join(sorted(FIELDS)))
        for key in FIELDS - {'evidence'}:
            cap = 4000 if key in ('summary', 'memory') else 2000
            if not isinstance(result[key], str) or len(result[key]) > cap or (key != 'memory' and not result[key].strip()):
                raise ValueError('invalid or over-limit result field: ' + key)
        if result['decision'] not in DECISIONS or not isinstance(result['evidence'], list):
            raise ValueError('invalid decision or evidence')
        if not result['evidence'] and result['decision'] not in ('blocked', 'inconclusive'):
            raise ValueError('this decision requires source evidence')
        if len(_json(result)) > 20000:
            raise ValueError('result exceeds 20000 characters')
        with self._db() as db:
            task = self._leased(db, task_id, worker_id)
            if result['decision'] == 'propose_improvement' and task['role'] != 'improvement_proposal':
                raise ValueError('only improvement_proposal can propose improvements')
            packet = json.loads(task['packet'])
            sources = {s['event_id']: s['content'] for s in packet['sources']}
            for item in result['evidence']:
                if not isinstance(item, dict) or set(item) != {'source_id', 'quote'} or not isinstance(item['source_id'], str) or not isinstance(item['quote'], str) or not item['quote'].strip() or item['source_id'] not in sources or item['quote'] not in sources[item['source_id']]:
                    raise ValueError('evidence must quote a source event in the frozen packet')
            if task['role'] == 'director_decision' and result['decision'] == 'continue':
                for dep in ('researcher', 'data_auditor', 'reviewer'):
                    row = db.execute('SELECT result FROM tasks WHERE cycle_id=? AND role=?', (task['cycle_id'], dep)).fetchone()
                    if not row['result'] or json.loads(row['result'])['decision'] != 'continue':
                        raise ValueError('continuation requires researcher, auditor and reviewer continuation')
            db.execute("UPDATE tasks SET state='completed', result=?, result_hash=? WHERE task_id=?", (_json(result), _hash(_json(result)), task_id))
            db.execute("UPDATE attempts SET ended_at=?, outcome='completed' WHERE task_id=? AND ended_at IS NULL", (_now(), task_id))
            db.execute('INSERT INTO decisions VALUES (?,?,?)', (task_id, result['decision'], _now()))
            candidate_id = packet['cycle']['candidate_id']
            version = db.execute('SELECT COALESCE(MAX(version),0)+1 FROM memory_history WHERE candidate_id=? AND role=?', (candidate_id, task['role'])).fetchone()[0]
            db.execute('INSERT INTO memory_history VALUES (?,?,?,?,?,?,?)', (candidate_id, task['role'], version, result['memory'], _hash(result['memory']), task_id, _now()))
            db.execute('INSERT OR REPLACE INTO memory_current VALUES (?,?,?)', (candidate_id, task['role'], version))
            return {'task_id': task_id, 'state': 'completed', 'decision': result['decision']}

    def _failure(self, db, task, reason):
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
            raise ValueError('failure requires a reason <=2000 characters')
        db.execute("UPDATE tasks SET state='failed', reason=? WHERE task_id=?", (reason, task['task_id']))
        db.execute("UPDATE attempts SET ended_at=?, outcome='failed', reason=? WHERE task_id=? AND ended_at IS NULL", (_now(), reason, task['task_id']))
        # Propagate failure eagerly, including across multiple dependency levels.
        blocked = {task['role']}
        for role in ROLES:
            if any(dep in blocked for dep in self._dependencies(role)):
                blocked.add(role)
                db.execute("UPDATE tasks SET state='blocked', reason=? WHERE cycle_id=? AND role=? AND state='pending'", ('dependency failed: ' + task['task_id'], task['cycle_id'], role))
        return {'task_id': task['task_id'], 'state': 'failed', 'reason': reason}

    def fail(self, task_id, worker_id, reason):
        with self._db() as db:
            return self._failure(db, self._leased(db, task_id, worker_id), reason)

    def recover(self, task_id, resolution='failed', reason=''):
        if resolution != 'failed':
            raise ValueError('recovery only supports failed; submit the retained lease or create a new cycle')
        with self._db() as db:
            return self._failure(db, self._leased(db, task_id), reason)

    def stop(self, reason):
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
            raise ValueError('stop requires a reason <=2000 characters')
        with self._db() as db:
            db.execute('UPDATE policy SET stopped=1, reason=? WHERE id=1', (reason,))
        return self.status()

    def resume(self):
        with self._db() as db:
            db.execute("UPDATE policy SET stopped=0, reason='' WHERE id=1")
        return self.status()

    def status(self):
        with self._db() as db:
            return {'policy': dict(db.execute('SELECT * FROM policy WHERE id=1').fetchone()), 'attempts_used': db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0], 'sources': db.execute('SELECT COUNT(*) FROM sources').fetchone()[0], 'cycles': [dict(r) for r in db.execute('SELECT * FROM cycles ORDER BY rowid')], 'tasks': [dict(r) for r in db.execute('SELECT task_id,cycle_id,role,state,worker_id,packet_hash,reason FROM tasks ORDER BY rowid')]}

    def get_task(self, task_id):
        """Inspect saved packets/results without redispatching retained leases."""
        with self._db() as db:
            row = db.execute('SELECT * FROM tasks WHERE task_id=?', (task_id,)).fetchone()
            if row is None:
                raise ValueError('unknown task')
            task = dict(row)
            for field in ('packet', 'result'):
                task[field] = json.loads(task[field]) if task[field] else None
            task['submission_errors'] = [dict(r) for r in db.execute('SELECT * FROM submission_errors WHERE task_id=? ORDER BY rowid', (task_id,))]
            task['attempts'] = [dict(r) for r in db.execute('SELECT * FROM attempts WHERE task_id=? ORDER BY rowid', (task_id,))]
            return task

    def director_brief(self, max_chars=6000):
        """Bounded routing context with final decision excerpts, never raw sources.

        This is distinct from coding-maintainer context and worker packets.
        Counts expose omitted entries; get_task is the explicit drill-down path.
        """
        if type(max_chars) is not int or max_chars < 1200 or max_chars > 20000:
            raise ValueError('max_chars must be an integer between 1200 and 20000')
        with self._db() as db:
            counts = {row['state']: row['n'] for row in db.execute('SELECT state,COUNT(*) AS n FROM tasks GROUP BY state')}
            pending_count = counts.get('pending', 0) + counts.get('leased', 0)
            total_decisions = db.execute("SELECT COUNT(*) FROM decisions d JOIN tasks t USING(task_id) WHERE t.role='director_decision'").fetchone()[0]
            tasks = [dict(r) for r in db.execute("SELECT t.task_id,t.cycle_id,t.role,t.state,t.worker_id FROM tasks t WHERE state IN ('pending','leased') ORDER BY CASE state WHEN 'leased' THEN 0 ELSE 1 END,t.rowid LIMIT 8")]
            decisions = [dict(r) for r in db.execute("SELECT d.task_id,t.cycle_id,t.role,d.decision,t.result_hash,t.result FROM decisions d JOIN tasks t USING(task_id) WHERE t.role='director_decision' ORDER BY d.rowid DESC LIMIT 8")]
            for decision in decisions:
                result = json.loads(decision.pop('result'))
                for field in ('summary', 'next_action'):
                    decision[field] = result[field][:300]
                    decision[field + '_truncated'] = len(result[field]) > 300
            policy = dict(db.execute('SELECT max_tasks,max_concurrent,stopped FROM policy WHERE id=1').fetchone())
        prompts = []
        if (self.root / 'research_state' / 'improvement.sqlite3').exists():
            from .improvement import ImprovementRegistry
            registry = ImprovementRegistry(self.root)
            for role in ROLES:
                active = registry.active(role)
                if active:
                    prompts.append({'role': role, 'id': active['id']})
        brief = {'context_owner': 'internal_research_director',
                 'objective': 'Establish document feasibility for frozen candidates; preserve failures and propose evaluated prompt improvements. No strategy validation or trading.',
                 'policy': policy, 'task_counts': counts, 'pending_and_leased': tasks,
                 'latest_decisions': decisions, 'active_prompt_ids': prompts,
                 'counts': {'pending_and_leased_total': pending_count, 'decisions_total': total_decisions, 'active_prompts_total': len(prompts)},
                 'limits': {'max_tasks_shown': 8, 'max_decisions_shown': 8, 'max_prompts_shown': len(ROLES), 'max_chars': max_chars}}
        for key, total in [('pending_and_leased', pending_count), ('latest_decisions', total_decisions), ('active_prompt_ids', len(prompts))]:
            brief['counts'][key + '_omitted'] = total - len(brief[key])
        while len(_json(brief)) > max_chars:
            key = next((k for k in ('latest_decisions', 'pending_and_leased', 'active_prompt_ids') if brief[k]), None)
            if key is None:
                raise ValueError('brief metadata exceeds max_chars')
            brief[key].pop()
            brief['counts'][key + '_omitted'] += 1
        return brief

    def list_sources(self):
        """Source metadata only. Full text stays behind get_task / ingest."""
        with self._db() as db:
            return [dict(r) for r in db.execute(
                'SELECT event_id, source_id, content_hash, published_at, received_at, revision, length(content) AS chars FROM sources ORDER BY rowid')]

    def role_report(self, role):
        """Audit slice for one role. Packets and results remain on get_task."""
        if role not in ROLES:
            raise ValueError('unknown role')
        with self._db() as db:
            tasks = [dict(r) for r in db.execute(
                'SELECT task_id, cycle_id, role, state, worker_id, packet_hash, result_hash, reason FROM tasks WHERE role=? ORDER BY rowid',
                (role,))]
            attempts = [dict(r) for r in db.execute(
                'SELECT a.* FROM attempts a JOIN tasks t ON t.task_id=a.task_id WHERE t.role=? ORDER BY a.rowid',
                (role,))]
            errors = [dict(r) for r in db.execute(
                'SELECT e.* FROM submission_errors e JOIN tasks t ON t.task_id=e.task_id WHERE t.role=? ORDER BY e.rowid',
                (role,))]
            memory = [dict(r) for r in db.execute(
                'SELECT candidate_id, role, version, memory, memory_hash, task_id, updated_at FROM memory_history WHERE role=? ORDER BY candidate_id, version',
                (role,))]
            current = [dict(r) for r in db.execute(
                'SELECT * FROM memory_current WHERE role=?', (role,))]
        open_task = next((t for t in tasks if t['state'] in ('pending', 'leased')), None)
        return {
            'role': role,
            'reviewer_blinded': role == 'reviewer',
            'open_task': open_task,
            'task_count': len(tasks),
            'attempt_count': len(attempts),
            'error_count': len(errors),
            'tasks': tasks,
            'attempts': attempts,
            'submission_errors': errors,
            'memory_history': memory,
            'memory_current': current,
        }
