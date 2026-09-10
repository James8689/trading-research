"""Map roles to provider/model/worker from env. Never returns secrets."""
from __future__ import annotations

from .envfile import key_hint
from .network import ROLES

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


def _parse_route(spec, env):
    spec = (spec or '').strip()
    if not spec:
        return None
    if ':' not in spec:
        raise ValueError('role routing must be provider:model')
    provider, model = spec.split(':', 1)
    provider = provider.strip().lower()
    model = model.strip()
    if provider not in PROVIDERS:
        raise ValueError(f'unknown provider {provider}; use openai, anthropic, or xai')
    if not model:
        model = (env.get(DEFAULT_MODELS[provider]) or '').strip()
    if not model:
        raise ValueError(f'no model id for provider {provider}')
    return provider, model


def role_route(role, env):
    if role not in ROLES:
        raise ValueError('unknown role')
    spec = env.get(ROLE_ENV[role], '')
    parsed = _parse_route(spec, env)
    meta = PROVIDERS[parsed[0]] if parsed else None
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


def provider_env_keys(provider):
    """Env variable names the console may set for one vendor."""
    provider = (provider or '').strip().lower()
    if provider not in PROVIDERS:
        raise ValueError('unknown provider; use openai, anthropic, or xai')
    meta = PROVIDERS[provider]
    return {'key': meta['key'], 'base': meta['base'], 'model': DEFAULT_MODELS[provider]}


def secret_for(route, env):
    if not route['provider']:
        raise RuntimeError('role has no provider mapping')
    secret = (env.get(PROVIDERS[route['provider']]['key']) or '').strip()
    if not secret:
        raise RuntimeError(f"no API key for {route['provider']} (role {route['role']})")
    return secret
