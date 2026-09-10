"""Load and edit a local .env without overriding a real process environment."""
from __future__ import annotations

from pathlib import Path
import os
import re

_LINE = re.compile(r'^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$')
_PRINTABLE = re.compile(r'[\x20-\x7e]*')
_SECRET_MAX = 8192
_VALUE_MAX = 400

# Only these may be written from the operator console. The login password and
# every budget knob stay out: the dashboard must never raise its own spend.
SECRET_KEYS = ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'XAI_API_KEY')
WRITABLE = (
    'OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL',
    'ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL', 'ANTHROPIC_MODEL',
    'XAI_API_KEY', 'XAI_BASE_URL', 'XAI_MODEL',
    'ROLE_DIRECTOR_PLAN', 'ROLE_RESEARCHER', 'ROLE_DATA_AUDITOR',
    'ROLE_REVIEWER', 'ROLE_DIRECTOR_DECISION', 'ROLE_IMPROVEMENT_PROPOSAL',
    'RESEARCH_MODELS', 'RESEARCH_PROVIDERS',
)
LOCKED = (
    'DASHBOARD_PASSWORD', 'RESEARCH_BUDGET_PERIOD', 'RESEARCH_BUDGET_LIMIT_USD',
    'RESEARCH_MAX_CALL_USD', 'RESEARCH_USD_PER_MTOK_INPUT', 'RESEARCH_USD_PER_MTOK_OUTPUT',
)
_CUSTOM_PROVIDER = re.compile(r'^PROVIDER_([A-Z][A-Z0-9]{0,20})_(API_KEY|BASE_URL|MODEL|KIND)$')


def is_secret_key(key):
    return key in SECRET_KEYS or bool(_CUSTOM_PROVIDER.fullmatch(key) and key.endswith('_API_KEY'))


def is_writable_key(key):
    if key in LOCKED:
        return False
    return key in WRITABLE or bool(_CUSTOM_PROVIDER.fullmatch(key))


def parse_env_text(text):
    values = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or line.startswith(';'):
            continue
        match = _LINE.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def load_env_file(path):
    path = Path(path)
    if not path.is_file():
        return {}
    return parse_env_text(path.read_text(encoding='utf-8-sig'))


def merged_env(root, environ=None, filename='.env'):
    """File values fill gaps only. Process env and explicit environ win."""
    environ = os.environ if environ is None else environ
    loaded = load_env_file(Path(root) / filename)
    merged = dict(loaded)
    for key, value in environ.items():
        merged[key] = value
    return merged


def apply_file_to_os(root, filename='.env'):
    """Set missing os.environ keys from the file. Never overwrite."""
    for key, value in load_env_file(Path(root) / filename).items():
        if key not in os.environ:
            os.environ[key] = value
    return os.environ


def usd_to_micro(value):
    if isinstance(value, int):
        if value < 0:
            raise ValueError('USD amount must be nonnegative')
        return value * 1_000_000
    if not isinstance(value, str) or not value.strip():
        raise ValueError('USD amount required')
    text = value.strip()
    if not re.fullmatch(r'\d+(\.\d{1,6})?', text):
        raise ValueError('USD amount must be a decimal number')
    dollars, _, cents = text.partition('.')
    frac = (cents + '000000')[:6]
    return int(dollars) * 1_000_000 + int(frac)


def key_hint(secret):
    if not secret:
        return None
    cleaned = secret.strip()
    if len(cleaned) < 4:
        return 'set'
    return cleaned[-4:]


def check_env_value(key, value):
    """Reject anything that would break the one-line KEY=value format."""
    if not isinstance(value, str):
        raise ValueError(f'{key} must be a string')
    cleaned = value.strip()
    if is_secret_key(key):
        cleaned = re.sub(r'\s+', '', cleaned)
        limit = _SECRET_MAX
    else:
        limit = _VALUE_MAX
    if len(cleaned) > limit:
        raise ValueError(f'{key} is longer than {limit} characters')
    if not _PRINTABLE.fullmatch(cleaned):
        raise ValueError(f'{key} must be printable ASCII on a single line')
    if '"' in cleaned or "'" in cleaned:
        raise ValueError(f'{key} cannot contain quote characters')
    return cleaned


def env_key_state(key, value):
    """Console-safe description of one variable. Secrets show last four only."""
    cleaned = (value or '').strip()
    secret = is_secret_key(key)
    return {
        'key': key,
        'secret': secret,
        'set': bool(cleaned),
        'value': None if secret else (cleaned or None),
        'hint': key_hint(cleaned) if secret else None,
    }


def env_state(env, root=None, filename='.env'):
    path = None if root is None else Path(root) / filename
    keys = list(WRITABLE)
    for key in env:
        if is_writable_key(key) and key not in keys:
            keys.append(key)
    return {
        'file': filename,
        'exists': bool(path and path.is_file()),
        'writable': [env_key_state(key, env.get(key)) for key in keys],
        'locked': list(LOCKED),
        'note': (
            'Keys are stored in the gitignored .env file and are never returned to the '
            'browser. Budget limits and the login password are edited in that file '
            'directly; the console cannot change them.'
        ),
    }


def _atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    handle = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(handle, 'w', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def write_env_values(root, updates, filename='.env'):
    """Update the allowlisted keys in .env in place, preserving comments.

    An empty value clears the variable. Every occurrence of a key is rewritten
    so a duplicated line cannot shadow the new value.
    """
    if not isinstance(updates, dict) or not updates:
        raise ValueError('no values to write')
    cleaned = {}
    for key, value in updates.items():
        if not is_writable_key(key):
            raise ValueError(f'{key} cannot be set from the console')
        cleaned[key] = check_env_value(key, value)
    path = Path(root) / filename
    lines = path.read_text(encoding='utf-8-sig').splitlines() if path.is_file() else []
    out, seen = [], set()
    for raw in lines:
        match = _LINE.match(raw.strip())
        key = match.group(1) if match else None
        if key in cleaned:
            out.append(f'{key}={cleaned[key]}')
            seen.add(key)
        else:
            out.append(raw)
    missing = [key for key in cleaned if key not in seen]
    if missing:
        if out and out[-1].strip():
            out.append('')
        out.append('# Added from the operator console.')
        out.extend(f'{key}={cleaned[key]}' for key in missing)
    _atomic_write(path, '\n'.join(out).rstrip('\n') + '\n')
    for key, value in cleaned.items():
        if value:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)
    return [env_key_state(key, cleaned[key]) for key in cleaned]
