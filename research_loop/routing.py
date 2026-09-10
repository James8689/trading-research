"""Map roles to provider/model/worker from env. Never returns secrets."""
from __future__ import annotations

import re

from .envfile import key_hint
from .network import ROLES

_ALIAS = re.compile(r'^[a-z][a-z0-9]{0,20}$')
_CUSTOM_KIND = re.compile(r'^PROVIDER_([A-Z][A-Z0-9]{0,20})_KIND$')
KINDS = ('openai', 'anthropic')
PROVIDERS_KEY = 'RESEARCH_PROVIDERS'

PROVIDERS = {
    'openai': {'key': 'OPENAI_API_KEY', 'base': 'OPENAI_BASE_URL', 'default_base': 'https://api.openai.com/v1', 'kind': 'openai'},
    'anthropic': {'key': 'ANTHROPIC_API_KEY', 'base': 'ANTHROPIC_BASE_URL', 'default_base': 'https://api.anthropic.com', 'kind': 'anthropic'},
    'xai': {'key': 'XAI_API_KEY', 'base': 'XAI_BASE_URL', 'default_base': 'https://api.x.ai/v1', 'kind': 'openai'},
}

ROLE_ENV = {
    'director_plan': 'ROLE_DIRECTOR_PLAN',
    'researcher': 'ROLE_RESEARCHER',
    'data_auditor': 'ROLE_DATA_AUDITOR',
    'reviewer': 'ROLE_REVIEWER',
    'director_decision': 'ROLE_DIRECTOR_DECISION',
    'improvement_proposal': 'ROLE_IMPROVEMENT_PROPOSAL',
}

# Director decision and improvement must share a worker identity.
WORKERS = {
    'director_plan': 'worker-director',
    'researcher': 'worker-researcher',
    'data_auditor': 'worker-auditor',
    'reviewer': 'worker-reviewer',
    'director_decision': 'worker-director',
    'improvement_proposal': 'worker-director',
}

DEFAULT_MODELS = {
    'openai': 'OPENAI_MODEL',
    'anthropic': 'ANTHROPIC_MODEL',
    'xai': 'XAI_MODEL',
}

# Muse is a planned vendor with a known OpenAI-compatible host. It is not a
# fourth built-in in PROVIDERS so operators can still override the alias.
MUSE_DEFAULT_BASE = 'https://api.meta.ai/v1'
MUSE_META = {
    'key': 'PROVIDER_MUSE_API_KEY',
    'base': 'PROVIDER_MUSE_BASE_URL',
    'default_base': MUSE_DEFAULT_BASE,
    'kind': 'openai',
    'custom': True,
}

# Old .env.example ids. Replaced when the matching vendor key is saved.
LEFTOVER_SPECS = frozenset({
    'openai:gpt-5.4',
    'xai:grok-4',
    'anthropic:claude-sonnet-4-6',
})

# design/OPPORTUNITY_ENGINE.md — labels and jobs, not verified callable IDs.
# One vendor may appear more than once (Sol and Astra are both openai).
MODELS_KEY = 'RESEARCH_MODELS'


def check_alias(alias):
    name = (alias or '').strip().lower()
    if not _ALIAS.fullmatch(name):
        raise ValueError('provider name must start with a letter and be at most 21 letters or digits')
    if name in PROVIDERS:
        raise ValueError(f'{name} is already a built-in; pick a different name')
    return name


def provider_aliases(env):
    """Custom provider names from RESEARCH_PROVIDERS and PROVIDER_*_KIND lines."""
    found = []
    for part in (env.get(PROVIDERS_KEY) or '').split(','):
        name = part.strip().lower()
        if name and name not in found and name not in PROVIDERS:
            found.append(name)
    for key in env:
        match = _CUSTOM_KIND.fullmatch(key)
        if not match:
            continue
        name = match.group(1).lower()
        if name not in found and name not in PROVIDERS:
            found.append(name)
    return found


def resolved_providers(env):
    """Built-in vendors plus any custom OpenAI-compatible or Anthropic endpoints."""
    providers = {name: dict(meta) for name, meta in PROVIDERS.items()}
    defaults = dict(DEFAULT_MODELS)
    providers['muse'] = dict(MUSE_META)
    defaults['muse'] = 'PROVIDER_MUSE_MODEL'
    for alias in provider_aliases(env or {}):
        prefix = f'PROVIDER_{alias.upper()}_'
        kind = ((env or {}).get(prefix + 'KIND') or 'openai').strip().lower()
        if kind not in KINDS:
            continue
        base = ((env or {}).get(prefix + 'BASE_URL') or '').rstrip('/')
        providers[alias] = {
            'key': prefix + 'API_KEY',
            'base': prefix + 'BASE_URL',
            'default_base': base,
            'kind': kind,
            'custom': True,
        }
        defaults[alias] = prefix + 'MODEL'
    return providers, defaults


SUGGESTED_STACK = (
    {
        'id': 'sol', 'label': 'Sol',
        'preference': 'GPT-5.6 Sol',
        'use': 'Normal orchestration',
        'provider': 'openai', 'model': 'gpt-5.6-sol', 'custom': False,
        'roles': ('director_plan', 'director_decision', 'improvement_proposal'),
    },
    {
        'id': 'astra', 'label': 'Astra',
        'preference': 'GPT-6 Astra',
        'use': 'Difficult / high-value escalation',
        'provider': 'openai', 'model': 'gpt-6-astra', 'custom': False,
        'roles': (),
    },
    {
        'id': 'muse', 'label': 'Muse Spark',
        'preference': 'Meta Muse Spark',
        'use': 'Inexpensive high-volume creativity and research',
        'provider': 'muse', 'model': 'muse-spark-1.3', 'custom': True,
        'roles': ('researcher',),
    },
    {
        'id': 'grok', 'label': 'Grok',
        'preference': 'Grok 4.6',
        'use': 'Independent checking and auditing',
        'provider': 'xai', 'model': 'grok-4.6', 'custom': False,
        'roles': ('data_auditor',),
    },
    {
        'id': 'sonnet', 'label': 'Sonnet',
        'preference': 'Claude Sonnet 5',
        'use': 'Adversarial falsification',
        'provider': 'anthropic', 'model': 'claude-sonnet-5', 'custom': False,
        'roles': ('reviewer',),
    },
)


def _parse_route(spec, env):
    spec = (spec or '').strip()
    if not spec:
        return None
    if ':' not in spec:
        raise ValueError('role routing must be provider:model')
    provider, model = spec.split(':', 1)
    provider = provider.strip().lower()
    model = model.strip()
    providers, defaults = resolved_providers(env)
    if provider not in providers:
        known = ', '.join(sorted(providers))
        raise ValueError(f'unknown provider {provider}; use {known} or add one in Budget')
    if not model:
        model = (env.get(defaults.get(provider, '')) or '').strip()
    if not model:
        raise ValueError(f'no model id for provider {provider}')
    return provider, model


def role_route(role, env):
    if role not in ROLES:
        raise ValueError('unknown role')
    spec = env.get(ROLE_ENV[role], '')
    parsed = _parse_route(spec, env)
    providers, _defaults = resolved_providers(env)
    meta = providers[parsed[0]] if parsed else None
    secret = (env.get(meta['key']) or '').strip() if meta else ''
    base = ''
    if meta:
        base = (env.get(meta['base']) or meta['default_base']).rstrip('/')
    return {
        'role': role,
        'worker_id': WORKERS[role],
        'configured': parsed is not None,
        'provider': parsed[0] if parsed else None,
        'model': parsed[1] if parsed else None,
        'kind': meta['kind'] if meta else None,
        'base_url': base or None,
        'has_key': bool(secret),
        'key_hint': key_hint(secret) if secret else None,
    }


def public_route(role, env):
    try:
        return role_route(role, env)
    except ValueError as exc:
        return {
            'role': role,
            'worker_id': WORKERS.get(role),
            'configured': False,
            'provider': None,
            'model': None,
            'kind': None,
            'base_url': None,
            'has_key': False,
            'key_hint': None,
            'error': str(exc),
        }


def public_routes(env):
    return [public_route(role, env) for role in ROLES]


def parse_model_list(text, env=None):
    """Parse RESEARCH_MODELS: comma-separated provider:model pairs."""
    env = env or {}
    items = []
    seen = set()
    for part in (text or '').split(','):
        spec = part.strip()
        if not spec:
            continue
        parsed = _parse_route(spec, env)
        if parsed is None:
            raise ValueError('each catalog entry must be provider:model')
        if parsed in seen:
            continue
        seen.add(parsed)
        items.append({'provider': parsed[0], 'model': parsed[1], 'spec': f'{parsed[0]}:{parsed[1]}'})
    return items


def encode_model_list(items):
    return ','.join(f"{item['provider']}:{item['model']}" for item in items)


def catalog_models(env):
    """Models the operator has named, plus anything already used by a role."""
    found, seen = [], set()

    def add(provider, model):
        provider = (provider or '').strip().lower()
        model = (model or '').strip()
        if not provider or not model or (provider, model) in seen:
            return
        providers, _defaults = resolved_providers(env)
        if provider not in providers:
            return
        seen.add((provider, model))
        secret = (env.get(providers[provider]['key']) or '').strip()
        found.append({
            'provider': provider,
            'model': model,
            'spec': f'{provider}:{model}',
            'has_key': bool(secret),
            'key_hint': key_hint(secret) if secret else None,
        })

    try:
        listed = parse_model_list(env.get(MODELS_KEY, ''), env)
    except ValueError:
        listed = []
    for item in listed:
        add(item['provider'], item['model'])
    _providers, defaults = resolved_providers(env)
    for provider, name in defaults.items():
        add(provider, env.get(name))
    for role in ROLES:
        route = public_route(role, env)
        if route['configured']:
            add(route['provider'], route['model'])
    return found


def _stack_match(item, catalog, routes):
    """Which catalog row, if any, currently stands in for this planned job.

    A leftover example model still counts as 'in catalog'. That is not the same
    as having a key — callers must check has_key separately.
    """
    by_spec = {row['spec']: row for row in catalog}
    if item['roles']:
        for route in routes:
            if route['role'] not in item['roles'] or not route.get('configured'):
                continue
            spec = f"{route['provider']}:{route['model']}"
            if spec in by_spec:
                return by_spec[spec]
    if item['id'] == 'astra':
        sol_roles = next(row['roles'] for row in SUGGESTED_STACK if row['id'] == 'sol')
        used = {
            f"{route['provider']}:{route['model']}"
            for route in routes
            if route['role'] in sol_roles and route.get('configured')
        }
        extras = [row for row in catalog if row['provider'] == 'openai' and row['spec'] not in used]
        if extras:
            return extras[0]
        if item['model']:
            return by_spec.get(f"{item['provider']}:{item['model']}")
        return None
    if item.get('custom'):
        return next((row for row in catalog if row['provider'] == item['provider']), None)
    if item['model']:
        spec = f"{item['provider']}:{item['model']}"
        if spec in by_spec:
            return by_spec[spec]
    if item['roles']:
        return next((row for row in catalog if row['provider'] == item['provider']), None)
    return None


def vendor_for_key(env_key, env=None):
    providers, _defaults = resolved_providers(env)
    for name, meta in providers.items():
        if meta['key'] == env_key:
            return name
    return None


def planned_seed_updates(pending, provider):
    """Catalog the planned models for one vendor and map leftover/empty roles."""
    pending = dict(pending)
    out = {}
    if provider == 'muse':
        aliases = [part.strip() for part in (pending.get(PROVIDERS_KEY) or '').split(',') if part.strip()]
        if 'muse' not in aliases:
            aliases.append('muse')
            out[PROVIDERS_KEY] = ','.join(aliases)
            pending[PROVIDERS_KEY] = out[PROVIDERS_KEY]
        if not (pending.get('PROVIDER_MUSE_KIND') or '').strip():
            out['PROVIDER_MUSE_KIND'] = 'openai'
            pending['PROVIDER_MUSE_KIND'] = 'openai'
        if not (pending.get('PROVIDER_MUSE_BASE_URL') or '').strip():
            out['PROVIDER_MUSE_BASE_URL'] = MUSE_DEFAULT_BASE
            pending['PROVIDER_MUSE_BASE_URL'] = MUSE_DEFAULT_BASE
    specs = [
        f"{item['provider']}:{item['model']}"
        for item in SUGGESTED_STACK
        if item['provider'] == provider and item['model']
    ]
    try:
        catalog = [item['spec'] for item in parse_model_list(pending.get(MODELS_KEY, ''), pending)]
    except ValueError:
        catalog = []
    leftovers = {spec for spec in LEFTOVER_SPECS if spec.startswith(f'{provider}:')}
    used = {(pending.get(var) or '').strip() for var in ROLE_ENV.values() if (pending.get(var) or '').strip()}
    catalog = [spec for spec in catalog if spec not in leftovers or spec in used]
    for spec in specs:
        if spec not in catalog:
            catalog.append(spec)
    out[MODELS_KEY] = ','.join(catalog)
    pending[MODELS_KEY] = out[MODELS_KEY]
    for item in SUGGESTED_STACK:
        if item['provider'] != provider or not item['model']:
            continue
        spec = f"{item['provider']}:{item['model']}"
        for role in item['roles']:
            name = ROLE_ENV[role]
            current = (pending.get(name) or '').strip()
            if not current or current in LEFTOVER_SPECS:
                out[name] = spec
                pending[name] = spec
    return out


def suggested_stack(env):
    catalog = catalog_models(env)
    routes = public_routes(env)
    rows = []
    for item in SUGGESTED_STACK:
        match = _stack_match(item, catalog, routes)
        planned = f"{item['provider']}:{item['model']}" if item['model'] else None
        rows.append({
            **{key: item[key] for key in (
                'id', 'label', 'preference', 'use', 'provider', 'model', 'roles', 'custom',
            )},
            'spec': match['spec'] if match else planned,
            'in_catalog': match is not None,
            'has_key': bool(match and match['has_key']),
            'key_hint': match['key_hint'] if match else None,
        })
    return rows


def validate_route_spec(spec, env):
    """Raise ValueError unless spec is a usable provider:model pair."""
    parsed = _parse_route(spec, env)
    if parsed is None:
        raise ValueError('role routing must be provider:model')
    return parsed


def validate_base_url(value):
    """Allow https anywhere, plain http only for a loopback proxy."""
    text = (value or '').strip()
    if not text:
        return ''
    if text.startswith('https://'):
        return text.rstrip('/')
    if text.startswith('http://'):
        host = text[7:].split('/', 1)[0].split(':', 1)[0]
        if host in {'127.0.0.1', 'localhost', '[::1]'}:
            return text.rstrip('/')
    raise ValueError('base URL must use https, or http on localhost')


def provider_env_keys(provider, env=None):
    """Env variable names the console may set for one vendor."""
    provider = (provider or '').strip().lower()
    providers, defaults = resolved_providers(env)
    if provider not in providers:
        known = ', '.join(sorted(providers))
        raise ValueError(f'unknown provider {provider}; use {known}')
    meta = providers[provider]
    return {
        'key': meta['key'],
        'base': meta['base'],
        'model': defaults[provider],
        'kind': meta['kind'],
        'custom': bool(meta.get('custom')),
    }


def secret_for(route, env):
    if not route['provider']:
        raise RuntimeError('role has no provider mapping')
    providers, _defaults = resolved_providers(env)
    if route['provider'] not in providers:
        raise RuntimeError(f"unknown provider {route['provider']}")
    secret = (env.get(providers[route['provider']]['key']) or '').strip()
    if not secret:
        raise RuntimeError(f"no API key for {route['provider']} (role {route['role']})")
    return secret
