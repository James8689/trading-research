"""Operator-facing internal director.

This is the designed director from NETWORK.md / ORCHESTRATION.md / CONTEXT_AND_RECOVERY.md:
a replaceable frontier model (Sol on director_plan) that operates the research
network through the controller. James talks to it in the console. It reads the
bounded brief, drills into a task only when needed, and may run existing
Network methods. It cannot raise spend, change its evaluator, waive gates, or
trade. Packet workers stay on the six-role graph; this chat is not a worker.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

from .budget import BudgetLedger
from .dispatch import apply_env_budget, dispatch_next, max_call_micro, actual_from_usage, run_cycle
from .envfile import merged_env
from .network import Network, ROLES
from .providers import ProviderError, complete
from .routing import role_route, secret_for

DIRECTOR_ROLE = 'director_plan'
MAX_ROUNDS = 8
MAX_DISPATCHES = 1
HISTORY_MESSAGES = 12
BODY_CHARS = 1500
TASK_CHARS = 8000

SYSTEM_PROMPT = """You are the internal research director of this Opportunity Engine.

The coding maintainer builds software. You operate research. James is the single operator talking to you in the console. A new director must be able to resume from repository state and the brief below; do not depend on a coding chat.

You own the mission and opportunity portfolio. Workers do accurate local science: a correct rejection, block, or falsification is success. You integrate partial views. You cannot waive deterministic controller rules: budgets, leases, hashes, provenance, frozen plans, or validation gates. You cannot approve your own prompt changes, rewrite the evaluator, raise spend, download URLs, or place broker orders.

Pipeline (one cycle graph): director_plan → independent researcher and data_auditor → blinded reviewer → director_decision → improvement_proposal. Same director identity owns plan, decision, and improvement. Reviewer packets exclude upstream interpretations. Empty polling must not invent work.

Context rules from the design: keep this conversation on the bounded brief (objective, at most two active experiments, gate/queue status, disagreements, budget, next actions). Retrieve a full task only with get_task when you must decide a gate or resolve a dispute. Never dump raw price series into prose. Memory is lossy; canonical records are SQLite artifacts.

When James asks for an update, call get_status and get_brief, then answer in plain language: what is waiting, what is leased, last decisions, spend, and the next smallest action. Do not claim a strategy is validated. continue from a worker means ready for the next bounded step, not live trading.

You may seed the frozen CEF document-feasibility cycle, park an idea, stop or resume claims, dispatch one ready packet, or run_cycle to walk at most six ready packets in graph order. That is a bounded operator run, not an unattended loop. If a required source is missing, the cycle should finish blocked and name what to ingest. Unusual ideas are allowed; incoherent mechanisms are not.

Talk like a colleague. Be specific. Cite task ids and decisions. If you cannot do something because the controller forbids it, say so and name the tool or setting James would need.
"""

TOOLS = [
    {
        'name': 'get_brief',
        'description': 'Bounded director resume capsule: objective, queue, latest decisions, prompt ids, omitted counts.',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'get_status',
        'description': 'Queue counts, stop flag, spend ledger (no secrets), freeze integrity, next claimable task.',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'list_pipeline',
        'description': 'The six roles and each open task state. No full packets.',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'get_task',
        'description': 'Exact saved packet/result for one task id. Use only to decide a gate or answer James about that task.',
        'parameters': {
            'type': 'object',
            'properties': {'task_id': {'type': 'string'}},
            'required': ['task_id'],
        },
    },
    {
        'name': 'seed_cef',
        'description': 'Register the frozen B3-H1-v1 CEF feasibility cycle and fill the queue. Idempotent. No model workers are called.',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'dispatch_one',
        'description': 'Lease the next ready packet (or a named role) and send it to its mapped model. One packet. Not a background loop.',
        'parameters': {
            'type': 'object',
            'properties': {
                'role': {
                    'type': 'string',
                    'enum': list(ROLES),
                    'description': 'Omit to dispatch the next ready role.',
                },
            },
        },
    },
    {
        'name': 'run_cycle',
        'description': 'Walk the ready CEF graph, at most six packets, then stop. Seed first if the queue is empty. Stops on budget, STOP, or a dispatch error. Not a background daemon.',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'stop',
        'description': 'Block new task claims. Open leases and the ledger stay. Reason is required.',
        'parameters': {
            'type': 'object',
            'properties': {'reason': {'type': 'string'}},
            'required': ['reason'],
        },
    },
    {
        'name': 'resume',
        'description': 'Admit task claims again. Existing leases were never dropped.',
        'parameters': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'park_idea',
        'description': 'Save an idea to the inbox without opening a cycle or calling a worker.',
        'parameters': {
            'type': 'object',
            'properties': {'text': {'type': 'string'}},
            'required': ['text'],
        },
    },
]


def director_route(env):
    route = role_route(DIRECTOR_ROLE, env)
    if not route['configured']:
        raise RuntimeError('director_plan has no ROLE_DIRECTOR_PLAN mapping in .env')
    if not route['has_key']:
        raise RuntimeError(f"director_plan is mapped to {route['provider']} but that API key is empty")
    return route


def director_ready(env, budget):
    try:
        route = director_route(env)
    except (RuntimeError, ValueError):
        return False
    return bool(route['has_key'] and budget.get('limit_microusd', 0) > 0 and not budget.get('blocked'))


def _clip(value, limit):
    encoded = json.dumps(value, ensure_ascii=False, default=str)
    if len(encoded) <= limit:
        return value
    return {'truncated': True, 'preview': encoded[:limit]}


def _history_messages(history):
    rows = []
    for item in (history or [])[-HISTORY_MESSAGES:]:
        author = item.get('author')
        body = (item.get('body') or '').strip()
        if not body or author not in ('james', 'director'):
            continue
        rows.append({
            'role': 'user' if author == 'james' else 'assistant',
            'content': body[:BODY_CHARS],
        })
    return rows


class DirectorSession:
    def __init__(self, root, env=None, store=None, transport=None, timeout=90):
        self.root = Path(root)
        self.env = merged_env(self.root, env)
        self.network = Network(self.root)
        self.budget = BudgetLedger(self.root)
        self.store = store
        self.transport = transport
        self.timeout = timeout
        self.dispatches = 0
        apply_env_budget(self.budget, self.env)

    def _public_budget(self):
        status = self.budget.status()
        return {
            'period_id': status['period_id'],
            'blocked': status['blocked'],
            'limit_usd': round(status['limit_microusd'] / 1e6, 6),
            'spent_usd': round(status['spent_microusd'] / 1e6, 6),
            'available_usd': round(status['available_microusd'] / 1e6, 6),
            'unknown_count': status['unknown_count'],
        }

    def _run_tool(self, name, arguments):
        arguments = arguments or {}
        if name == 'get_brief':
            return self.network.director_brief()
        if name == 'get_status':
            status = self.network.status()
            tasks = status.get('tasks') or []
            next_claim = next((t for t in tasks if t['state'] == 'pending'), None)
            return {
                'policy': status.get('policy'),
                'counts': _counts(tasks),
                'next_claimable': next_claim,
                'cycles': status.get('cycles'),
                'sources': status.get('sources'),
                'budget': self._public_budget(),
                'freeze': _freeze_status(self.root),
            }
        if name == 'list_pipeline':
            tasks = self.network.status().get('tasks') or []
            by_role = []
            for role in ROLES:
                open_task = next((t for t in tasks if t['role'] == role and t['state'] in ('pending', 'leased')), None)
                by_role.append({
                    'role': role,
                    'open': open_task,
                    'completed': sum(1 for t in tasks if t['role'] == role and t['state'] == 'completed'),
                })
            return {'roles': by_role}
        if name == 'get_task':
            task_id = (arguments.get('task_id') or '').strip()
            if not task_id:
                raise ValueError('task_id required')
            return _clip(self.network.get_task(task_id), TASK_CHARS)
        if name == 'seed_cef':
            from research_loop.__main__ import seed_cef
            return seed_cef(self.root, self.network, [])
        if name == 'dispatch_one':
            if self.dispatches >= MAX_DISPATCHES:
                raise RuntimeError('this turn already dispatched one packet; ask James to continue for the next')
            role = arguments.get('role') or None
            if role == '':
                role = None
            value = dispatch_next(self.root, role=role, env=self.env, transport=self.transport, timeout=self.timeout)
            self.dispatches += 1
            result = value.get('result') or {}
            return {
                'ok': True,
                'role': value.get('role'),
                'model': value.get('model'),
                'task_id': value.get('task_id'),
                'decision': result.get('decision'),
                'summary': (result.get('summary') or '')[:400],
            }
        if name == 'run_cycle':
            if self.dispatches:
                raise RuntimeError('this turn already dispatched; ask James to run the cycle as a separate request')
            value = run_cycle(self.root, env=self.env, transport=self.transport, timeout=self.timeout)
            self.dispatches = MAX_DISPATCHES
            return value
        if name == 'stop':
            reason = (arguments.get('reason') or '').strip()
            if not reason:
                raise ValueError('stop requires a reason')
            return self.network.stop(reason)
        if name == 'resume':
            return self.network.resume()
        if name == 'park_idea':
            text = (arguments.get('text') or '').strip()
            if not text:
                raise ValueError('idea text required')
            if self.store is None:
                return {'parked': False, 'reason': 'idea inbox is only available from the console'}
            return self.store.add_idea(text)
        raise ValueError(f'unknown tool {name}')

    def talk(self, text, history=None):
        text = (text or '').strip()
        if not text:
            raise ValueError('message body required')
        if self.budget.status()['blocked'] or self.budget.status()['limit_microusd'] <= 0:
            raise RuntimeError('budget admission denied; set RESEARCH_BUDGET_PERIOD and RESEARCH_BUDGET_LIMIT_USD')
        route = director_route(self.env)
        secret = secret_for(route, self.env)
        brief = self.network.director_brief()
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'system', 'content': 'Current bounded brief:\n' + json.dumps(brief, ensure_ascii=False)},
            *_history_messages(history),
            {'role': 'user', 'content': text},
        ]
        tools_used = []
        usages = []
        last_text = ''
        for _ in range(MAX_ROUNDS):
            completion = self._complete(route, secret, messages)
            usages.append(completion.get('usage') or {})
            last_text = (completion.get('text') or '').strip()
            calls = completion.get('tool_calls') or []
            if not calls:
                break
            assistant = {'role': 'assistant', 'content': last_text or None, 'tool_calls': [
                {
                    'id': call['id'],
                    'type': 'function',
                    'function': {
                        'name': call['name'],
                        'arguments': json.dumps(call['arguments']),
                    },
                    'name': call['name'],
                    'arguments': call['arguments'],
                }
                for call in calls
            ]}
            messages.append(assistant)
            for call in calls:
                try:
                    payload = self._run_tool(call['name'], call['arguments'])
                    error = None
                except (ValueError, RuntimeError, TypeError, OSError, KeyError) as exc:
                    payload = None
                    error = str(exc)
                tools_used.append({'name': call['name'], 'error': error})
                messages.append({
                    'role': 'tool',
                    'tool_call_id': call['id'],
                    'content': json.dumps({'ok': error is None, 'result': payload, 'error': error}, ensure_ascii=False, default=str)[:12000],
                })
        else:
            last_text = last_text or 'I hit the tool-round cap for this turn. Ask me to continue.'
        if not last_text:
            last_text = 'I ran the controller actions but had nothing further to say. Ask for /status if you want the numbers.'
        if len(last_text) > 8000:
            last_text = last_text[:8000]
        return {
            'ok': True,
            'reply': last_text,
            'role': route['role'],
            'provider': route['provider'],
            'model': route['model'],
            'tools': tools_used,
            'usage': _sum_usage(usages),
            'budget': self._public_budget(),
            'brief': brief,
        }

    def _complete(self, route, secret, messages):
        attempt_id = 'director_' + uuid.uuid4().hex
        reserved = max_call_micro(self.env)
        self.budget.reserve(attempt_id, reserved)
        dispatched = False
        usage = None
        try:
            completion = complete(
                route, secret, messages,
                timeout=self.timeout, transport=self.transport,
                json_mode=False, tools=TOOLS,
            )
            self.budget.record_dispatch(attempt_id, completion['request_id'])
            dispatched = True
            usage = completion.get('usage')
            self.budget.settle(attempt_id, actual_from_usage(self.env, usage, reserved))
            return completion
        except (ProviderError, ValueError, RuntimeError, OSError, TimeoutError) as exc:
            if 'timeout' in str(exc).lower() and not dispatched:
                self.budget.settle(attempt_id, None)
            elif dispatched:
                self.budget.settle(attempt_id, actual_from_usage(self.env, usage, reserved))
            else:
                self.budget.settle(attempt_id, 0)
            raise RuntimeError(str(exc)) from exc


def _freeze_status(root):
    plan = Path(root) / 'research_batch3' / 'frozen_experiment_plans.json'
    receipt = Path(root) / 'research_batch3' / 'freeze_receipt.json'
    if not plan.is_file() or not receipt.is_file():
        return {'ok': False, 'reason': 'frozen plan or receipt missing'}
    digest = hashlib.sha256(plan.read_bytes()).hexdigest()
    expected = json.loads(receipt.read_text())['sha256']
    return {'ok': digest == expected, 'matches_receipt': digest == expected}


def _counts(tasks):
    tallies = {}
    for task in tasks:
        tallies[task['state']] = tallies.get(task['state'], 0) + 1
    return tallies


def _sum_usage(rows):
    prompt = sum((row.get('prompt_tokens') or 0) for row in rows)
    completion = sum((row.get('completion_tokens') or 0) for row in rows)
    return {'prompt_tokens': prompt, 'completion_tokens': completion}


def talk(root, text, history=None, env=None, store=None, transport=None, timeout=90):
    return DirectorSession(root, env=env, store=store, transport=transport, timeout=timeout).talk(text, history)
