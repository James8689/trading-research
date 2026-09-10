"""Bounded HTTP adapters. Stdlib only. No broker calls."""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


def default_transport(url, headers, body, timeout):
    req = Request(url, data=json.dumps(body).encode('utf-8'), headers=headers, method='POST')
    try:
        with urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode('utf-8'))
            return response.status, payload
    except HTTPError as exc:
        detail = exc.read().decode('utf-8', 'replace')[:500]
        raise ProviderError(f'provider HTTP {exc.code}: {detail}') from exc
    except URLError as exc:
        raise ProviderError(f'provider unreachable: {exc.reason}') from exc
    except TimeoutError as exc:
        raise ProviderError('provider timeout') from exc


def _usage(prompt_tokens, completion_tokens):
    return {
        'prompt_tokens': int(prompt_tokens or 0),
        'completion_tokens': int(completion_tokens or 0),
    }


def complete_openai(route, secret, messages, timeout=60, transport=None):
    transport = transport or default_transport
    url = route['base_url'].rstrip('/') + '/chat/completions'
    headers = {
        'Authorization': f'Bearer {secret}',
        'Content-Type': 'application/json',
    }
    body = {
        'model': route['model'],
        'messages': messages,
        'response_format': {'type': 'json_object'},
        'temperature': 0,
    }
    status, payload = transport(url, headers, body, timeout)
    if status >= 400 or not isinstance(payload, dict):
        raise ProviderError(f'openai-compatible error status={status}')
    choices = payload.get('choices') or []
    if not choices or not isinstance(choices[0], dict):
        raise ProviderError('openai-compatible response missing choices')
    message = (choices[0].get('message') or {}).get('content')
    usage = payload.get('usage') or {}
    return {
        'text': message if isinstance(message, str) else '',
        'request_id': str(payload.get('id') or payload.get('system_fingerprint') or 'openai-unknown'),
        'usage': _usage(usage.get('prompt_tokens'), usage.get('completion_tokens')),
    }


def complete_anthropic(route, secret, messages, timeout=60, transport=None):
    transport = transport or default_transport
    url = route['base_url'].rstrip('/') + '/v1/messages'
    system = ''
    converted = []
    for item in messages:
        if item['role'] == 'system':
            system = item['content']
        else:
            converted.append({'role': item['role'], 'content': item['content']})
    headers = {
        'x-api-key': secret,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json',
    }
    body = {'model': route['model'], 'max_tokens': 4096, 'temperature': 0, 'messages': converted}
    if system:
        body['system'] = system
    status, payload = transport(url, headers, body, timeout)
    if status >= 400 or not isinstance(payload, dict):
        raise ProviderError(f'anthropic error status={status}')
    blocks = payload.get('content') or []
    text = ''
    if blocks and isinstance(blocks[0], dict):
        text = blocks[0].get('text') or ''
    usage = payload.get('usage') or {}
    return {
        'text': text if isinstance(text, str) else '',
        'request_id': str(payload.get('id') or 'anthropic-unknown'),
        'usage': _usage(usage.get('input_tokens'), usage.get('output_tokens')),
    }


def complete(route, secret, messages, timeout=60, transport=None):
    if route['kind'] == 'anthropic':
        return complete_anthropic(route, secret, messages, timeout, transport)
    if route['kind'] == 'openai':
        return complete_openai(route, secret, messages, timeout, transport)
    raise ProviderError(f"unsupported provider kind {route.get('kind')}")
