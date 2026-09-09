"""Save a resumable research checkpoint, without credentials or trading actions."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,sys,datetime
ROOT=Path(__file__).resolve().parent
batch=ROOT/'alpaca_batches';batch.mkdir(exist_ok=True)
entries=[]
for p in sorted(batch.glob('*.json')):
    if p.name=='manifest.json':continue
    raw=p.read_bytes();d=json.loads(raw)
    entries.append({'file':p.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
        'request':d.get('request'), 'counts':d.get('counts'),
        'saved_bars':{k:len(v) for k,v in d.get('bars',{}).items()}})
manifest={'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':entries,
    'note':'Only listed files are completed. Preserve all files when resuming; do not refetch completed batches.'}
(batch/'manifest.json').write_text(json.dumps(manifest,indent=2))
if '--save' not in sys.argv:
    print(json.dumps({'files':len(entries),'bars':sum(sum(x['saved_bars'].values()) for x in entries)}));sys.exit()
dest=ROOT/'deliverables'/'Trading_Research_Checkpoint.zip';dest.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(ROOT)
        if rel.parts[0] in ['raw','figures','sources','__pycache__']:continue
        if rel.parts[0]=='deliverables' and p.suffix!='.md':continue
        if p.suffix=='.zip' or p.name=='checkpoint_receipt.json':continue
        z.write(p,Path('trading_research')/rel)
receipt=ROOT/'checkpoint_receipt.json'
up={'local_path':str(dest),'purpose':'create_library_file'}
if receipt.exists():
    prev=json.loads(receipt.read_text())
    up.update(purpose='replace_library_file',library_file_id=prev['library_file_id'],expected_current_version=prev['current_version_number'],version_reason='Completed historical data batches and updated research handoff')
helper='/root/.codex/plugins/cache/openai-curated-remote/openai-library/0.1.54/skills/library/scripts/library_upload.py'
r=subprocess.run(['/usr/bin/python3',helper],input=json.dumps({'uploads':[up]}),text=True,capture_output=True)
if r.returncode:
    print('Checkpoint upload failed or uncertain; do not automatically retry.',r.stderr);sys.exit(1)
d=json.loads(r.stdout);result=d['results'][0]
if result.get('status')!='succeeded':print(json.dumps(d));sys.exit(1)
receipt.write_text(json.dumps(result,indent=2))
print(json.dumps({'status':'saved','version':result.get('current_version_number'),'library_file_id':result.get('library_file_id'),'local_path':str(dest),'completed_files':len(entries),'bytes':dest.stat().st_size}))
