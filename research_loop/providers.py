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


def _openai_tools(tools):
    converted = []
    for item in tools or []:
        converted.append({
            'type': 'function',
            'function': {
                'name': item['name'],
                'description': item.get('description') or '',
                'parameters': item.get('parameters') or {'type': 'object', 'properties': {}},
            },
        })
    return converted


def _tool_calls_from_openai(message):
    found = []
    for item in message.get('tool_calls') or []:
        if not isinstance(item, dict):
            continue
        fn = item.get('function') or {}
        raw = fn.get('arguments') or '{}'
        try:
            arguments = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}
        found.append({
            'id': str(item.get('id') or fn.get('name') or 'tool'),
            'name': str(fn.get('name') or ''),
            'arguments': arguments,
        })
    return [row for row in found if row['name']]


def complete_openai(route, secret, messages, timeout=60, transport=None, json_mode=True, tools=None):
    transport = transport or default_transport
    url = route['base_url'].rstrip('/') + '/chat/completions'
    headers = {
        'Authorization': f'Bearer {secret}',
        'Content-Type': 'application/json',
    }
    body = {
        'model': route['model'],
        'messages': messages,
        'temperature': 0 if json_mode else 0.3,
    }
    if json_mode:
        body['response_format'] = {'type': 'json_object'}
    if tools:
        body['tools'] = _openai_tools(tools)
        body['tool_choice'] = 'auto'
    status, payload = transport(url, headers, body, timeout)
    if status >= 400 or not isinstance(payload, dict):
        raise ProviderError(f'openai-compatible error status={status}')
    choices = payload.get('choices') or []
    if not choices or not isinstance(choices[0], dict):
        raise ProviderError('openai-compatible response missing choices')
    message = choices[0].get('message') or {}
    text = message.get('content')
    usage = payload.get('usage') or {}
    return {
        'text': text if isinstance(text, str) else '',
        'tool_calls': _tool_calls_from_openai(message),
        'request_id': str(payload.get('id') or payload.get('system_fingerprint') or 'openai-unknown'),
        'usage': _usage(usage.get('prompt_tokens'), usage.get('completion_tokens')),
    }


def _anthropic_tools(tools):
    converted = []
    for item in tools or []:
        converted.append({
            'name': item['name'],
            'description': item.get('description') or '',
            'input_schema': item.get('parameters') or {'type': 'object', 'properties': {}},
        })
    return converted


def _anthropic_messages(messages):
    system = ''
    converted = []
    for item in messages:
        role = item.get('role')
        if role == 'system':
            chunk = item.get('content') or ''
            system = (system + '\n\n' + chunk).strip() if system else chunk
            continue
        if role == 'tool':
            converted.append({
                'role': 'user',
                'content': [{
                    'type': 'tool_result',
                    'tool_use_id': item.get('tool_call_id') or '',
                    'content': item.get('content') or '',
                }],
            })
            continue
        content = item.get('content')
        tool_calls = item.get('tool_calls') or []
        if tool_calls:
            blocks = []
            if isinstance(content, str) and content:
                blocks.append({'type': 'text', 'text': content})
            for call in tool_calls:
                blocks.append({
                    'type': 'tool_use',
                    'id': call.get('id') or call.get('name'),
                    'name': call.get('name'),
                    'input': call.get('arguments') or {},
                })
            converted.append({'role': 'assistant', 'content': blocks})
            continue
        if role == 'assistant':
            converted.append({'role': 'assistant', 'content': content or ''})
        else:
            converted.append({'role': 'user', 'content': content or ''})
    return system, converted


def complete_anthropic(route, secret, messages, timeout=60, transport=None, json_mode=True, tools=None):
    transport = transport or default_transport
    url = route['base_url'].rstrip('/') + '/v1/messages'
    system, converted = _anthropic_messages(messages)
    headers = {
        'x-api-key': secret,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json',
    }
    body = {
        'model': route['model'],
        'max_tokens': 4096,
        'temperature': 0 if json_mode else 0.3,
        'messages': converted,
    }
    if system:
        body['system'] = system
    if tools:
        body['tools'] = _anthropic_tools(tools)
    status, payload = transport(url, headers, body, timeout)
    if status >= 400 or not isinstance(payload, dict):
        raise ProviderError(f'anthropic error status={status}')
    blocks = payload.get('content') or []
    text = ''
    tool_calls = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get('type') == 'text' and not text:
            text = block.get('text') or ''
        if block.get('type') == 'tool_use' and block.get('name'):
            arguments = block.get('input') or {}
            if not isinstance(arguments, dict):
                arguments = {}
            tool_calls.append({
                'id': str(block.get('id') or block['name']),
                'name': str(block['name']),
                'arguments': arguments,
            })
    usage = payload.get('usage') or {}
    return {
        'text': text if isinstance(text, str) else '',
        'tool_calls': tool_calls,
        'request_id': str(payload.get('id') or 'anthropic-unknown'),
        'usage': _usage(usage.get('input_tokens'), usage.get('output_tokens')),
    }


def complete(route, secret, messages, timeout=60, transport=None, json_mode=True, tools=None):
    kwargs = {'timeout': timeout, 'transport': transport, 'json_mode': json_mode, 'tools': tools}
    if route['kind'] == 'anthropic':
        return complete_anthropic(route, secret, messages, **kwargs)
    if route['kind'] == 'openai':
        return complete_openai(route, secret, messages, **kwargs)
    raise ProviderError(f"unsupported provider kind {route.get('kind')}")
