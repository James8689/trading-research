"""Read-only source inventory; no strategy replay, network, or broker calls."""
from pathlib import Path
import hashlib, json, datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
files = []
patterns = ['*plan.json', 'AGENTS.md', 'HANDOFF.md', 'NEXT_AGENT_DIRECTION.md',
            'README.md', 'analysis/*results.json', 'analysis/*audit.json',
            'analysis/final_diagnostics.json', 'daily_results/results.json',
            'daily_results/data_audit.json', 'volume_results/results.json',
            'volume_results/data_audit.json', 'volume_results/attribution.json',
            'deliverables/Trading_Research_Update.md']
for p in sorted({p for pat in patterns for p in ROOT.glob(pat)}):
    raw = p.read_bytes()
    entry = {'path': p.relative_to(ROOT).as_posix(), 'bytes': len(raw),
             'sha256': hashlib.sha256(raw).hexdigest()}
    if p.suffix == '.json':
        data = json.loads(raw)
        entry['type'] = type(data).__name__
        entry['entries'] = len(data) if hasattr(data, '__len__') else None
        if isinstance(data, dict): entry['keys'] = list(data)[:20]
    files.append(entry)
summary = {
    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'purpose': 'Archive structure and valid JSON audit; no performance recalculation',
    'source_files': files,
    'eliminated_families': ['sector rebound', 'closing momentum', 'opening breakout',
        'overnight drift', 'trend/volatility allocation', 'volume shock continuation'],
    'historical_contamination': '2011-2025 evaluated; 2026 through September 4 partly inspected; none reserved for new confirmation',
    'current_status': 'No strategy validated; no trading authorization',
    'new_return_tests_run': 0}
(OUT/'archive_audit.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({'audited_files': len(files), 'invalid_json_files': 0,
                  'new_return_tests_run': 0}))
