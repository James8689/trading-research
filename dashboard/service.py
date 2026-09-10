"""Read/write facade. All research mutations go through controller classes."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sqlite3

from research_loop.budget import BudgetLedger
from research_loop.dispatch import apply_env_budget, dispatch_next
from research_loop.envfile import WRITABLE, env_state, merged_env, write_env_values
from research_loop.families import FamilyRegistry
from research_loop.improvement import ImprovementRegistry
from research_loop.network import ROLES, Network
from research_loop.routing import (
    PROVIDERS, ROLE_ENV, provider_env_keys, public_route, public_routes,
    validate_base_url, validate_route_spec,
)
from research_loop.__main__ import initialize_runtime, seed_cef


def _money(microusd):
    return {'microusd': microusd, 'usd': round(microusd / 1_000_000, 6)}


class Dashboard:
    def __init__(self, root):
        self.root = Path(root)
        initialize_runtime(self.root)
        self.network = Network(self.root)
        self.budget = BudgetLedger(self.root)
        self.improvement = ImprovementRegistry(self.root)
        self.families = FamilyRegistry(self.root)
        self.families.initialize()
        self.env = merged_env(self.root)
        if (self.root / '.env').is_file():
            apply_env_budget(self.budget, self.env)

    def freeze_status(self):
        plan = self.root / 'research_batch3' / 'frozen_experiment_plans.json'
        receipt = self.root / 'research_batch3' / 'freeze_receipt.json'
        if not plan.is_file() or not receipt.is_file():
            return {'ok': False, 'reason': 'frozen plan or receipt missing'}
        digest = hashlib.sha256(plan.read_bytes()).hexdigest()
        expected = json.loads(receipt.read_text())['sha256']
        return {'ok': digest == expected, 'sha256': digest, 'matches_receipt': digest == expected}

    def overview(self):
        try:
            status = self.network.status()
            brief = self.network.director_brief()
        except sqlite3.Error as exc:
            raise RuntimeError('research network is not initialized') from exc
        budget = self._budget()
        prompts = self.improvement.status()
        families = self.families.status()
        freeze = self.freeze_status()
        tasks = status.get('tasks', [])
        by_state = {}
        for task in tasks:
            by_state[task['state']] = by_state.get(task['state'], 0) + 1
        next_claim = next((t for t in tasks if t['state'] == 'pending'), None)
        routes = public_routes(self.env)
        return {
            'mode': 'assisted_manual',
            'provider_dispatch': self._dispatch_ready(budget, routes),
            'routes': routes,
            'broker_execution': False,
            'spend_approved': budget['limit_microusd'] > 0,
            'freeze': freeze,
            'policy': status.get('policy'),
            'attempts_used': status.get('attempts_used'),
            'sources': status.get('sources'),
            'task_counts': by_state,
            'cycles': status.get('cycles'),
            'tasks': tasks,
            'next_claimable': next_claim,
            'brief': brief,
            'budget': budget,
            'prompts': prompts['active'],
            'families': families,
            'roles': list(ROLES),
        }

    def _dispatch_ready(self, budget=None, routes=None):
        budget = self._budget() if budget is None else budget
        routes = public_routes(self.env) if routes is None else routes
        return budget['limit_microusd'] > 0 and not budget['blocked'] and any(r['has_key'] for r in routes)

    def env_view(self):
        """Which provider variables are set, without ever returning a secret."""
        budget = self._budget()
        return {
            **env_state(self.env, self.root),
            'roles': dict(ROLE_ENV),
            'providers': {name: provider_env_keys(name) for name in PROVIDERS},
            'routes': public_routes(self.env),
            'budget_period': budget['period_id'],
            'budget_configured': budget['limit_microusd'] > 0,
            'dispatch_ready': self._dispatch_ready(budget),
        }

    def save_env(self, updates):
        """Persist allowlisted provider settings to the gitignored .env file."""
        if not isinstance(updates, dict) or not updates:
            raise ValueError('values object required')
        unknown = [key for key in updates if key not in WRITABLE]
        if unknown:
            raise ValueError(f"cannot set {', '.join(sorted(unknown))} from the console")
        pending = dict(self.env)
        for key, value in updates.items():
            if isinstance(value, str):
                pending[key] = value.strip()
        role_vars = set(ROLE_ENV.values())
        for key, value in updates.items():
            text = value.strip() if isinstance(value, str) else value
            if not text:
                continue
            if key in role_vars:
                validate_route_spec(text, pending)
            elif key.endswith('_BASE_URL'):
                validate_base_url(text)
        saved = write_env_values(self.root, updates)
        self.env = merged_env(self.root)
        return {'saved': saved, **self.env_view()}

    def _budget(self):
        status = self.budget.status()
        status['spent'] = _money(status['spent_microusd'])
        status['reserved'] = _money(status['reserved_microusd'])
        status['limit'] = _money(status['limit_microusd'])
        status['available'] = _money(status['available_microusd'])
        status['note'] = (
            'Ledger is fail-closed. Unknown-cost attempts block new admissions. '
            'A period cap cannot be raised in place; change RESEARCH_BUDGET_PERIOD to open a new period '
            'only from the placeholder $0 ledger. Keys live in gitignored .env, never in this UI.'
        )
        return status

    def role(self, name):
        report = self.network.role_report(name)
        active = self.improvement.active(name)
        report['active_prompt'] = None if active is None else {
            'id': active['id'], 'role': active['role'], 'status': active.get('status'),
            'rationale': active.get('rationale'), 'parent_id': active.get('parent_id'),
        }
        report['prompt_history'] = [
            row for row in self.improvement.status()['history'] if row['role'] == name
        ]
        report['route'] = public_route(name, self.env)
        return report

    def task(self, task_id):
        task = self.network.get_task(task_id)
        if task.get('role') == 'reviewer':
            task['blinding'] = (
                'Reviewer packets exclude upstream interpretations. The dashboard '
                'still lets you open the saved packet for audit; do not paste that '
                'context back into a reviewer worker.'
            )
        return task

    def spend(self):
        return {
            'ledger': self._budget(),
            'routes': public_routes(self.env),
            'attribution': 'Role→model maps come from .env. Secrets are never returned. Each dispatch settles usage or the per-call reservation.',
        }

    def dispatch(self, role=None):
        return dispatch_next(self.root, role=role or None, env=self.env)

    def seed_cef(self, evidence=None):
        return seed_cef(self.root, self.network, evidence or [])

    def ingest(self, source_id, content, published_at=None):
        return self.network.ingest(source_id, content, published_at)

    def claim(self, worker_id, role=None):
        packet = self.network.claim(worker_id, role)
        if packet is None:
            return {'claimed': False, 'reason': 'no eligible task (stopped, caps, unmet deps, or identity conflict)'}
        return {'claimed': True, 'packet': packet}

    def submit(self, task_id, worker_id, result):
        return self.network.submit(task_id, worker_id, result)

    def fail(self, task_id, worker_id, reason):
        return self.network.fail(task_id, worker_id, reason)

    def stop(self, reason):
        return self.network.stop(reason)

    def resume(self):
        return self.network.resume()

    def brief(self):
        return self.network.director_brief()
