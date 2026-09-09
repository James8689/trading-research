"""Post-result attribution, not new strategy selection or a tradable portfolio."""
import json
import numpy as np
import pandas as pd
import test_volume_shock as v

F={**v.F,**v.t.FRAMES}
adjopen={s:(f.adjusted*f.open/f.close).reindex(v.DATES) for s,f in F.items()}
allrows=[];summary=[]
for horizon in [5,20]:
 for e in v.event_records:
  i=e['event_index']+1;j=i+horizon
  if j>=len(v.DATES):continue
  s=e['symbol'];price=adjopen[s]
  ret=price.iloc[j]/price.iloc[i]-1
  peers=[x for x in v.GROUPS[e['group']] if x!=s]
  peer=float(np.nanmean([adjopen[x].iloc[j]/adjopen[x].iloc[i]-1 for x in peers]))
  qqq=adjopen['QQQ'].iloc[j]/adjopen['QQQ'].iloc[i]-1
  allrows.append({**e,'entry_date':str(v.DATES[i].date()),'exit_date':str(v.DATES[j].date()),'horizon':horizon,
      'stock_gross':ret,'peer_excess':ret-peer,'qqq_excess':ret-qqq,'stock_net_10bps':(1+ret)*(1-.0005)/(1+.0005)-1})
df=pd.DataFrame(allrows)
for split,start,end in [('all','2011-01-01','2025-12-31'),('reserved','2022-01-01','2025-12-31')]:
 dates=v.DATES[(v.DATES>=start)&(v.DATES<=end)]
 for h in [5,20]:
  g=df[(df.horizon==h)&(df.entry_date>=start)&(df.exit_date<=end)].copy()
  for metric in ['stock_net_10bps','peer_excess','qqq_excess']:
   by=g.groupby('entry_date')[metric].agg(['sum','count']).reindex(dates.astype(str)).fillna(0)
   for block in [20,60]:
    n=len(by);rng=np.random.default_rng(1207);starts=rng.integers(0,n,(3000,int(np.ceil(n/block))))
    inds=((starts[:,:,None]+np.arange(block))%n).reshape(3000,-1)[:,:n]
    den=by['count'].to_numpy()[inds].sum(axis=1);num=by['sum'].to_numpy()[inds].sum(axis=1)
    means=num[den>0]/den[den>0];ci=np.quantile(means,[.025,.975])
    summary.append({'split':split,'horizon':h,'metric':metric,'events':len(g),'mean':g[metric].mean(),
        'block_sessions':block,'ci95':ci.tolist()})
trades=pd.DataFrame(json.loads((v.OUT/'trades.json').read_text()))
concentration=[]
for split in ['all','reserved']:
 g=trades[(trades.split==split)&(trades.horizon==20)&(trades.roundtrip_cost_bps==10)]
 by=g.groupby('symbol').pnl.sum().sort_values(ascending=False)
 concentration.append({'split':split,'total_pnl':g.pnl.sum(),'by_symbol':by.to_dict(),
  'top_five_trades_pnl':g.nlargest(5,'pnl').pnl.sum(),'top_five_trades':g.nlargest(5,'pnl').to_dict('records'),
  'bottom_five_trades':g.nsmallest(5,'pnl').to_dict('records')})
(v.OUT/'attribution.json').write_text(json.dumps({'note':'Post-result descriptive fixed-horizon diagnostic; all signal events, no stops, no capital constraints. Peer and QQQ excess are gross relative returns, not alpha estimates. Entry-date blocks preserve clustered observations; intervals do not adjust for the broader research search.',
  'event_results':summary,'concentration':concentration},indent=2))
print(json.dumps([x for x in summary if x['split']=='reserved' and x['horizon']==20 and x['block_sessions']==20],indent=2))
print(json.dumps([{k:c[k] for k in ['split','total_pnl','top_five_trades_pnl','by_symbol']} for c in concentration],indent=2))
