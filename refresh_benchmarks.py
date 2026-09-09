"""Correct benchmark to fully reinvested fractional total return, no strategy changes."""
import test_daily as t
import json,pandas as pd,numpy as np
results=json.loads((t.OUT/'results.json').read_text());results=[x for x in results if x['method']!='buy_hold']
curves=json.loads((t.OUT/'daily_curves.json').read_text());curves=[x for x in curves if x['method']!='buy_hold']
for split,start,end in [('all','2011-01-01','2025-12-31'),('development','2011-01-01','2021-12-31'),('reserved','2022-01-01','2025-12-31')]:
 for base in ['SPY','QQQ']:
  for cost in t.COSTS:
   rows=t.run(base,base,'buy_hold',cost,start,end);r=t.stats(rows)
   r.update(split=split,base=base,etf=base,method='buy_hold',roundtrip_cost_bps=cost,start=rows[0]['date'],end=rows[-1]['date'])
   results.append(r)
   if split=='all':curves.extend(rows)
   if cost==5:print(json.dumps(r),flush=True)
(t.OUT/'results.json').write_text(json.dumps(results,indent=2));(t.OUT/'daily_curves.json').write_text(json.dumps(curves,indent=2))
annual=[];df=pd.DataFrame(curves)
for (base,method,cost,year),g in df.groupby(['base','method','roundtrip_cost_bps',df.date.str[:4]]):
 r=g.account_return.to_numpy();eq=np.r_[1,np.cumprod(1+r)]
 annual.append({'base':base,'method':method,'roundtrip_cost_bps':int(cost),'year':int(year),'total_return':float(eq[-1]-1),
  'drawdown':float((eq/np.maximum.accumulate(eq)-1).min()),'orders':int(g.orders.sum())})
(t.OUT/'annual_results.json').write_text(json.dumps(annual,indent=2))
