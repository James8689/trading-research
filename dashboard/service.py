"""Read/write facade. All research mutations go through controller classes."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sqlite3

from research_loop.budget import BudgetLedger
from research_loop.director_chat import director_ready, talk as director_talk
from research_loop.dispatch import apply_env_budget, dispatch_next, run_cycle
from research_loop.envfile import is_writable_key, env_state, merged_env, write_env_values
from research_loop.families import FamilyRegistry
from research_loop.improvement import ImprovementRegistry
from research_loop.network import ROLES, Network
from research_loop.routing import (
    KINDS, MODELS_KEY, MUSE_DEFAULT_BASE, PROVIDERS_KEY, ROLE_ENV, catalog_models,
    check_alias, parse_model_list, planned_seed_updates, provider_aliases,
    provider_env_keys, public_route, public_routes, resolved_providers,
    suggested_stack, validate_base_url, validate_route_spec, vendor_for_key,
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
            'director_live': director_ready(self.env, budget),
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
            'providers': {
                name: provider_env_keys(name, self.env)
                for name in resolved_providers(self.env)[0]
            },
            'models': catalog_models(self.env),
            'stack': suggested_stack(self.env),
            'routes': public_routes(self.env),
            'budget_period': budget['period_id'],
            'budget_configured': budget['limit_microusd'] > 0,
            'dispatch_ready': self._dispatch_ready(budget),
        }

    def save_env(self, updates):
        """Persist allowlisted provider settings to the gitignored .env file."""
        if not isinstance(updates, dict) or not updates:
            raise ValueError('values object required')
        unknown = [key for key in updates if not is_writable_key(key)]
        if unknown:
            raise ValueError(f"cannot set {', '.join(sorted(unknown))} from the console")
        pending = dict(self.env)
        for key, value in updates.items():
            if isinstance(value, str):
                pending[key] = value.strip()
        seeded = {}
        for key, value in list(updates.items()):
            text = value.strip() if isinstance(value, str) else ''
            if not key.endswith('_API_KEY') or not text:
                continue
            vendor = vendor_for_key(key, pending)
            if vendor:
                seeded.update(planned_seed_updates(pending, vendor))
        if seeded:
            updates = dict(updates)
            updates.update(seeded)
            pending.update(seeded)
        role_vars = set(ROLE_ENV.values())
        for key, value in updates.items():
            text = value.strip() if isinstance(value, str) else value
            if not text:
                continue
            if key in role_vars:
                validate_route_spec(text, pending)
            elif key == MODELS_KEY:
                parse_model_list(text, pending)
            elif key == PROVIDERS_KEY:
                for alias in text.split(','):
                    if alias.strip():
                        check_alias(alias)
            elif key.endswith('_KIND'):
                if text not in KINDS:
                    raise ValueError('API style must be openai or anthropic')
            elif key.endswith('_BASE_URL'):
                validate_base_url(text)
        for alias in provider_aliases(pending):
            prefix = f'PROVIDER_{alias.upper()}_'
            base = (pending.get(prefix + 'BASE_URL') or '').strip()
            if alias == 'muse' and not base:
                base = MUSE_DEFAULT_BASE
                pending[prefix + 'BASE_URL'] = base
                updates[prefix + 'BASE_URL'] = base
            if (pending.get(prefix + 'KIND') or pending.get(prefix + 'API_KEY') or pending.get(prefix + 'MODEL')) and not base:
                raise ValueError(f'{alias} needs a base URL (https, or http on localhost)')
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

    def run_cycle(self, transport=None):
        return run_cycle(self.root, env=self.env, transport=transport)

    def talk(self, text, history=None, store=None, transport=None):
        return director_talk(self.root, text, history=history, env=self.env, store=store, transport=transport)

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
