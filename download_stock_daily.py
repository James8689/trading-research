"""Bounded public historical-data download. Research only, no trading API."""
from pathlib import Path
import json,urllib.request,datetime as dt,hashlib,concurrent.futures
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'daily_raw';OUT.mkdir(exist_ok=True)
start=int(dt.datetime(2010,1,1,tzinfo=dt.timezone.utc).timestamp());end=int(dt.datetime(2026,9,8,tzinfo=dt.timezone.utc).timestamp())
def fetch(s):
 p=OUT/f'{s}.json'
 if p.exists():raw=p.read_bytes();url='cached; see prior manifest'
 else:
  url=f'https://query1.finance.yahoo.com/v8/finance/chart/{s}?period1={start}&period2={end}&interval=1d&includePrePost=false&events=div%2Csplits'
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:raw=r.read()
  p.write_bytes(raw)
 j=json.loads(raw)['chart']['result'][0]
 result={'symbol':s,'url':url,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'granularity':j['meta'].get('dataGranularity'),'rows':len(j.get('timestamp',[])),'events':{k:len(v) for k,v in j.get('events',{}).items()}}
 if result['granularity']!='1d':raise ValueError(f'{s}: returned {result["granularity"]}, not daily')
 return result
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 futures={pool.submit(fetch,s):s for s in [x for g in json.loads((ROOT/'groups.json').read_text()).values() for x in g]}
 for f in concurrent.futures.as_completed(futures):
  try:r=f.result()
  except Exception as e:r={'symbol':futures[f],'error':str(e)}
  results.append(r);print(json.dumps(r),flush=True)
(OUT/'stock_manifest.json').write_text(json.dumps(results,indent=2))
