"""Portable offline entry point: python go.py [--mode demo|start|check|dashboard]."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=['demo', 'start', 'check', 'dashboard'], default='demo')
    p.add_argument('--report', help='Optional new JSON report path (will not overwrite)')
    args = p.parse_args(argv)
    if sys.version_info < (3, 11):
        p.error('Python 3.11 or newer is required. No third-party packages needed for the network.')
    if args.report and Path(args.report).exists():
        p.error('Report already exists; choose a new path')
    try:
        if args.mode == 'dashboard':
            from research_loop.envfile import apply_file_to_os
            apply_file_to_os(ROOT)
            from dashboard.server import serve
            return serve(ROOT)
        if args.mode == 'check':
            subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=ROOT, check=True)
            subprocess.run([sys.executable, 'scripts/verify_repository.py'], cwd=ROOT, check=True)
            value = {'status': 'checks_passed'}
        elif args.mode == 'demo':
            from research_loop.demo import run_demo
            value = run_demo()
        else:
            from research_loop.__main__ import initialize_runtime, seed_cef
            from research_loop.network import Network
            # Bootstrapping is idempotent and never resets existing policy or prompts.
            initialize_runtime(ROOT)
            network = Network(ROOT)
            cycle = seed_cef(ROOT, network, [])
            value = {'mode': 'assisted_manual', 'cycle_id': cycle['cycle_id'],
                     'brief': network.director_brief(),
                     'next_command': 'python -m research_loop next director --role director_plan',
                     'note': 'Queue prepared. No language-model process started. Import original evidence before a source-review cycle.'}
        encoded = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
        if args.report:
            with Path(args.report).open('x', encoding='utf-8') as stream:
                stream.write(encoded)
        print(encoded, end='')
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'go: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
