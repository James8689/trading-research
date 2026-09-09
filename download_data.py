"""Download public data for exploratory research. Contains no trading code."""
from pathlib import Path
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw'
RAW.mkdir(parents=True, exist_ok=True)
GROUPS = {
    'software': ['MSFT', 'AAPL', 'ORCL', 'CRM'],
    'semiconductors': ['NVDA', 'AMD', 'AVGO', 'QCOM', 'MU', 'INTC'],
    'finance': ['JPM', 'BAC', 'C', 'WFC', 'GS', 'MS'],
    'energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB'],
    'retail': ['AMZN', 'WMT', 'TGT', 'COST', 'HD', 'LOW'],
    'industrial': ['CAT', 'DE', 'HON', 'GE', 'RTX', 'BA'],
    'communication': ['META', 'GOOGL', 'NFLX', 'DIS'],
}
STOCKS = [x for v in GROUPS.values() for x in v]
ETFS = ['SPY', 'QQQ', 'TQQQ', 'SQQQ', 'UPRO', 'SPXU']
TASKS = [(s,'60d','5m') for s in STOCKS+ETFS]
TASKS += [(s,'730d','1h') for s in ETFS]
TASKS += [(s,'max','1d') for s in ETFS]

def fetch(task):
    symbol, period, interval = task
    path=RAW / f'{symbol}_{interval}.json'
    url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={period}&interval={interval}&includePrePost=false&events=div%2Csplits'
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=25) as r:
            data=r.read()
        obj=json.loads(data)
        result=obj['chart']['result'][0]
        timestamps=result['timestamp']
        path.write_bytes(data)
        row={'symbol':symbol,'interval':interval,'url':url,'bytes':len(data),
             'sha256':hashlib.sha256(data).hexdigest(),'bars':len(timestamps),
             'first_utc':dt.datetime.fromtimestamp(timestamps[0],dt.timezone.utc).isoformat(),
             'last_utc':dt.datetime.fromtimestamp(timestamps[-1],dt.timezone.utc).isoformat(),
             'retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
        print(json.dumps({k:row[k] for k in ['symbol','interval','bars','first_utc','last_utc']}),flush=True)
        return row
    except Exception as e:
        print(json.dumps({'symbol':symbol,'interval':interval,'error':str(e)}),flush=True)
        return {'symbol':symbol,'interval':interval,'url':url,'error':str(e)}

if __name__=='__main__':
    (ROOT/'groups.json').write_text(json.dumps(GROUPS,indent=2))
    with cf.ThreadPoolExecutor(max_workers=5) as pool:
        rows=list(pool.map(fetch,TASKS))
    (ROOT/'data_manifest.json').write_text(json.dumps(rows,indent=2))
    print('Successful:',sum('error' not in r for r in rows),'of',len(rows),flush=True)
