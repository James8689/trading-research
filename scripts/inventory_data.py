"""Catalog existing cached data, never fetch or change it."""
from pathlib import Path
import json, hashlib
ROOT=Path(__file__).resolve().parents[1]
files=[]
for folder in ('raw','daily_raw','alpaca_batches','analysis','daily_results','volume_results','sources','figures'):
    for p in sorted((ROOT/folder).glob('*')):
        if p.is_file():
            files.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,
                          'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'data_inventory.json').write_text(json.dumps({'purpose':'Private project preservation, not a market-data redistribution license','files':files},indent=2))
print(json.dumps({'files':len(files),'bytes':sum(x['bytes'] for x in files)}))
