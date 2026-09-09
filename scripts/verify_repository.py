"""Offline data/hash, plan and source checks. No import of historical simulators."""
from pathlib import Path
import ast, hashlib, json, sys

ROOT = Path(__file__).resolve().parents[1]
def check():
    errors = []
    source_count = 0
    for p in ROOT.rglob('*.py'):
        if any(x in p.parts for x in ('.git','.venv','venv','.research_runtime')): continue
        source_count += 1
        try: ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
        except Exception as exc: errors.append(f'{p.relative_to(ROOT)}: {type(exc).__name__}')
    receipt = ROOT/'research_batch3/freeze_receipt.json'
    if receipt.exists():
        d = json.loads(receipt.read_text())
        if hashlib.sha256((receipt.parent/d['file']).read_bytes()).hexdigest() != d['sha256']:
            errors.append('Frozen plan hash mismatch')
    manifest = ROOT/'data_inventory.json'
    checked = 0
    if manifest.exists():
        for row in json.loads(manifest.read_text())['files']:
            p=ROOT/row['path']; checked+=1
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
                errors.append('Data hash mismatch: '+row['path'])
    print(json.dumps({'python_sources_parsed':source_count,'data_files_verified':checked,'errors':errors}))
    return bool(errors)
if __name__ == '__main__': sys.exit(check())
