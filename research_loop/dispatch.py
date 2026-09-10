"""One leased packet → one provider call. No unattended loop. No broker."""
from __future__ import annotations

import json
import uuid

from .budget import BudgetLedger
from .envfile import merged_env, usd_to_micro
from .network import FIELDS, Network, ROLES
from .providers import ProviderError, complete
from .routing import public_routes, role_route, secret_for

PLACEHOLDER_PERIOD = 'manual-no-spend'
RESULT_INSTRUCTION = (
    'Return ONLY a JSON object with exactly these keys: '
    'summary, decision, evidence, uncertainty, next_action, memory. '
    'decision must be one of continue, reject, blocked, inconclusive, review_required, propose_improvement. '
    'evidence is a list of {source_id, quote} objects using source event_id values from the packet. '
    'Empty evidence is allowed only for blocked or inconclusive. '
    'Do not place broker orders, download URLs, or change frozen experiment rules.'
)


def apply_env_budget(ledger, env):
    period = (env.get('RESEARCH_BUDGET_PERIOD') or '').strip()
    limit_text = (env.get('RESEARCH_BUDGET_LIMIT_USD') or '').strip()
    if not period or not limit_text:
        return {'applied': False, 'reason': 'budget env unset'}
    limit = usd_to_micro(limit_text)
    status = ledger.status()
    if status['period_id'] is None:
        ledger.initialize(period, limit)
        return {'applied': True, 'reason': 'initialized', **ledger.status()}
    if status['period_id'] == period and status['limit_microusd'] == limit:
        return {'applied': False, 'reason': 'already_open', **status}
    if status['period_id'] == PLACEHOLDER_PERIOD and status['limit_microusd'] == 0:
        ledger.open_period(period, limit)
        return {'applied': True, 'reason': 'replaced_placeholder', **ledger.status()}
    if status['period_id'] != period:
        return {'applied': False, 'reason': 'different_period_exists', 'current_period': status['period_id'], **status}
    raise ValueError('cannot change limit on an existing period')


def max_call_micro(env):
    text = (env.get('RESEARCH_MAX_CALL_USD') or '0.50').strip()
    value = usd_to_micro(text)
    if value < 1:
        raise ValueError('RESEARCH_MAX_CALL_USD must be positive')
    return value


def actual_from_usage(env, usage, reserved):
    inn = (env.get('RESEARCH_USD_PER_MTOK_INPUT') or '').strip()
    out = (env.get('RESEARCH_USD_PER_MTOK_OUTPUT') or '').strip()
    if not inn or not out or not usage:
        return reserved
    prompt = usage.get('prompt_tokens') or 0
    completion = usage.get('completion_tokens') or 0
    micro = int(prompt * usd_to_micro(inn) / 1_000_000 + completion * usd_to_micro(out) / 1_000_000)
    return min(reserved, max(0, micro))


def _extract_json(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('model returned empty text')
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.strip('`')
        if cleaned.startswith('json'):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find('{'), cleaned.rfind('}')
        if start < 0 or end <= start:
            raise ValueError('model did not return JSON')
        value = json.loads(cleaned[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError('model JSON must be an object')
    missing = FIELDS - set(value)
    if missing:
        raise ValueError('model JSON missing required result fields')
    return {key: value[key] for key in FIELDS}


def dispatch_next(root, role=None, env=None, transport=None, timeout=60):
    env = merged_env(root, env)
    network = Network(root)
    budget = BudgetLedger(root)
    budget_note = apply_env_budget(budget, env)
    last_error = None
    for chosen in _candidate_roles(network, role):
        route = role_route(chosen, env)
        if not route['configured']:
            last_error = f'{chosen} has no ROLE_* mapping in .env'
            continue
        if not route['has_key']:
            last_error = f"{chosen} is mapped to {route['provider']} but that API key is empty"
            continue
        if budget.status()['blocked'] or budget.status()['limit_microusd'] <= 0:
            raise RuntimeError('budget admission denied; set RESEARCH_BUDGET_PERIOD and RESEARCH_BUDGET_LIMIT_USD')
        reserved = max_call_micro(env)
        tasks = network.status().get('tasks') or []
        leased = next((t for t in tasks if t['role'] == chosen and t['state'] == 'leased'), None)
        if leased:
            packet = network.get_task(leased['task_id'])['packet']
            if packet is None:
                raise RuntimeError('leased task has no packet')
            worker_id = leased['worker_id']
        else:
            worker_id = route['worker_id']
            packet = network.claim(worker_id, chosen)
            if packet is None:
                last_error = f'{chosen} is not claimable yet (deps, caps, stop, or identity)'
                continue
        return _run_call(network, budget, env, route, packet, worker_id, reserved, budget_note, timeout, transport)
    raise RuntimeError(last_error or 'no pending or leased task to dispatch')


def _candidate_roles(network, role):
    if role:
        if role not in ROLES:
            raise ValueError('unknown role')
        return [role]
    ordered = []
    for task in network.status().get('tasks') or []:
        if task['state'] in ('leased', 'pending') and task['role'] not in ordered:
            ordered.append(task['role'])
    return ordered


def _run_call(network, budget, env, route, packet, worker_id, reserved, budget_note, timeout, transport):
    attempt_id = 'spend_' + uuid.uuid4().hex
    budget.reserve(attempt_id, reserved)
    messages = [
        {'role': 'system', 'content': packet.get('prompt', '') + '\n\n' + RESULT_INSTRUCTION},
        {'role': 'user', 'content': json.dumps(packet, ensure_ascii=False)},
    ]
    dispatched = False
    usage = None
    try:
        completion = complete(route, secret_for(route, env), messages, timeout=timeout, transport=transport)
        budget.record_dispatch(attempt_id, completion['request_id'])
        dispatched = True
        usage = completion.get('usage')
        result = _extract_json(completion['text'])
        submitted = network.submit(packet['task_id'], worker_id, result)
        actual = actual_from_usage(env, usage, reserved)
        settled = budget.settle(attempt_id, actual)
        return {
            'ok': True,
            'role': route['role'],
            'provider': route['provider'],
            'model': route['model'],
            'task_id': packet['task_id'],
            'worker_id': worker_id,
            'request_id': completion['request_id'],
            'usage': usage,
            'budget': settled,
            'budget_note': budget_note,
            'result': submitted,
        }
    except (ProviderError, ValueError, RuntimeError, OSError, TimeoutError) as exc:
        if 'timeout' in str(exc).lower() and not dispatched:
            budget.settle(attempt_id, None)
        elif dispatched:
            budget.settle(attempt_id, actual_from_usage(env, usage, reserved))
        else:
            budget.settle(attempt_id, 0)
        raise RuntimeError(str(exc)) from exc
