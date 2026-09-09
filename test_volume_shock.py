"""Frozen volume-shock experiment. Offline research only; no order API."""
from pathlib import Path
import json, math
import numpy as np
import pandas as pd
import test_daily as t

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'volume_results';OUT.mkdir(exist_ok=True)
GROUPS=json.loads((ROOT/'groups.json').read_text());GROUP={s:g for g,ss in GROUPS.items() for s in ss}
DATES=t.FRAMES['SPY'].index
F={s:t.load(s) for s in GROUP}
A={s:f.reindex(DATES).to_dict('list') for s,f in F.items()}
EVENTS={};event_records=[]
market=t.FRAMES['SPY'].cash_total_return
for s,f in F.items():
 residual=f.cash_total_return-market.reindex(f.index)
 vol=residual.rolling(20).std().shift(1)
 # Yahoo volumes are split-adjusted; this product preserves nominal dollar turnover.
 dollars=f.close*f.volume/f.future_split
 sig=(residual>=np.maximum(.03,1.5*vol))&(f.volume>=2*f.volume.rolling(20).mean().shift(1))
 sig&=(f.close>=f.low+.75*(f.high-f.low))&(f.close>=5)&(dollars.rolling(20).mean().shift(1)>=20e6)
 sig&=f.split.ne(1).rolling(20,min_periods=20).sum().eq(0)
 for date in f.index[sig]:
  i=DATES.get_loc(date)
  e={'symbol':s,'group':GROUP[s],'event_date':str(date.date()),'event_index':int(i),
    'score':float(residual.loc[date]/vol.loc[date]),'residual':float(residual.loc[date]),'stop':float(f.loc[date,'low']-.01)}
  EVENTS.setdefault(i+1,[]).append(e);event_records.append(e)
for events in EVENTS.values():events.sort(key=lambda e:(-e['score'],e['symbol']))

def simulate(horizon,cost,start,end):
 inds=np.where((DATES>=start)&(DATES<=end))[0]
 cash=2500.;equity=2500.;positions={};rows=[];trades=[];corporate=[];rate=cost/20000
 for k,i in enumerate(inds):
  previous=equity;fees=0.;orders=0
  def exit_position(s,price,reason):
   nonlocal cash,fees,orders
   p=positions.pop(s);amount=p['qty']*price;fee=amount*rate
   cash+=amount-fee;fees+=fee;orders+=1
   trades.append({**p,'symbol':s,'exit_date':str(DATES[i].date()),'exit_price':price,'exit_reason':reason,
     'pnl':amount-fee+p['dividends']-p['entry_notional']-p['entry_fee'],
     'return':(amount-fee+p['dividends'])/(p['entry_notional']+p['entry_fee'])-1})
  # Corporate actions affect only shares owned before the ex-date.
  for s,p in list(positions.items()):
   b=A[s];ratio=b['split'][i]
   assert np.isfinite(b['open'][i]),f'Missing held bar {s} {DATES[i]}'
   if ratio!=1:
    p['qty']*=ratio;p['stop']/=ratio
    corporate.append({'symbol':s,'date':str(DATES[i].date()),'ratio':ratio})
   dividend=p['qty']*b['dividend'][i];cash+=dividend;p['dividends']+=dividend
   if b['open'][i]<=p['stop']:exit_position(s,b['open'][i],'gap_stop')
   elif i>=p['exit_index']:exit_position(s,b['open'][i],'time')
  # Rank and size entirely on information available at this open.
  for e in EVENTS.get(i,[]):
   s=e['symbol'];b=A[s]
   if len(positions)>=4:break
   if any(p['group']==e['group'] for p in positions.values()):continue
   price=b['open'][i];stop=e['stop']/b['split'][i]
   if not np.isfinite(price) or price<=stop:continue
   eq_open=cash+sum(p['qty']*A[z]['open'][i] for z,p in positions.items())
   risk=price-stop+rate*(price+stop)
   qty=math.floor(min(.25*eq_open/(price*(1+rate)),.005*eq_open/risk,cash/(price*(1+rate))))
   if qty<1:continue
   amount=qty*price;fee=amount*rate;cash-=amount+fee;fees+=fee;orders+=1
   positions[s]={'qty':float(qty),'initial_qty':qty,'group':e['group'],'stop':stop,'exit_index':int(i+horizon),
    'entry_date':str(DATES[i].date()),'event_date':e['event_date'],'entry_price':price,'entry_notional':amount,
    'entry_fee':fee,'dividends':0.,'planned_risk':qty*risk,'score':e['score']}
  for s,p in list(positions.items()):
   if A[s]['low'][i]<=p['stop']:exit_position(s,p['stop'],'intraday_stop')
  marked=sum(p['qty']*A[s]['close'][i] for s,p in positions.items())
  equity=cash+marked;weight=marked/equity
  if k==len(inds)-1:
   for s in list(positions):exit_position(s,A[s]['close'][i],'end')
   equity=cash
  assert cash>=-1e-7 and equity>0
  rows.append({'date':str(DATES[i].date()),'equity':equity,'account_return':equity/previous-1,
     'fee':fees,'orders':orders,'weight':weight})
 assert abs(sum(x['pnl'] for x in trades)-(equity-2500))<1e-6
 return rows,trades,corporate

def equal_weight(cost,start,end):
 """Fractional monthly equal weight in available members; total-return accounting.
 Yahoo adjusted close/open ratio uses same-day adjustment factors; reinvested
 returns neutralize future factor scaling. Constituent eligibility needs 20 bars.
 """
 inds=np.where((DATES>=start)&(DATES<=end))[0];cash=2500.;equity=cash;pos={};rows=[];rate=cost/20000
 adjusted={s:f.adjusted.reindex(DATES).to_numpy() for s,f in F.items()}
 adjopen={s:adjusted[s]*np.array(A[s]['open'])/np.array(A[s]['close']) for s in F}
 first={s:DATES.get_loc(f.index[20]) for s,f in F.items()}
 for k,i in enumerate(inds):
  prev=equity;fee=0.;orders=0
  if k==0 or DATES[i].month!=DATES[inds[k-1]].month:
   available=[s for s in F if first[s]<i and np.isfinite(adjopen[s][i])]
   atopen=cash+sum(q*adjopen[s][i] for s,q in pos.items());target=atopen/len(available)
   turnover=sum(abs(target-pos.get(s,0)*adjopen[s][i]) for s in available)
   fee=turnover*rate;net=atopen-fee
   pos={s:net/len(available)/adjopen[s][i] for s in available};cash=0.;orders=len(available)
  equity=cash+sum(q*adjusted[s][i] for s,q in pos.items())
  if k==len(inds)-1:fee+=equity*rate;equity*=1-rate;orders+=len(pos)
  rows.append({'date':str(DATES[i].date()),'equity':equity,'account_return':equity/prev-1,'fee':fee,'orders':orders,'weight':1.})
 return rows

def main():
 results=[];allcurves=[];alltrades=[];allcorp=[]
 for split,start,end in [('all','2011-01-01','2025-12-31'),('development','2011-01-01','2021-12-31'),('reserved','2022-01-01','2025-12-31')]:
  for cost in [5,10,20]:
   for horizon in [5,20]:
    rows,trades,corp=simulate(horizon,cost,start,end)
    tags={'split':split,'horizon':horizon,'roundtrip_cost_bps':cost,'method':'volume_shock'}
    result={**t.stats(rows),**tags,'trades':len(trades),'wins':sum(x['pnl']>0 for x in trades),
      'stop_fraction':sum('stop' in x['exit_reason'] for x in trades)/len(trades) if trades else 0,
      'mean_trade_pnl':float(np.mean([x['pnl'] for x in trades])) if trades else 0,
      'corporate_actions_while_held':corp}
    results.append(result)
    if split in ['reserved','all'] and cost==10:print(json.dumps(result),flush=True)
    alltrades.extend([{**x,**tags} for x in trades]);allcorp.extend([{**x,**tags} for x in corp])
    if split=='all':allcurves.extend([{**r,**tags} for r in rows])
   rows=equal_weight(cost,start,end)
   tags={'split':split,'roundtrip_cost_bps':cost,'method':'same_universe_equal_weight'}
   result={**t.stats(rows),**tags};results.append(result)
   if cost==10:print(json.dumps(result),flush=True)
   if split=='all':allcurves.extend([{**r,**tags} for r in rows])
 for name,data in [('results',results),('trades',alltrades),('daily_curves',allcurves),('events',event_records),('data_audit',t.AUDIT),('corporate_actions_held',allcorp)]:
  (OUT/f'{name}.json').write_text(json.dumps(data,indent=2))
 annual=[];df=pd.DataFrame(allcurves);df['horizon']=df.horizon.fillna(0)
 for (method,h,c,yr),g in df.groupby(['method','horizon','roundtrip_cost_bps',df.date.str[:4]]):
  r=g.account_return.to_numpy();eq=np.r_[1,np.cumprod(1+r)]
  annual.append({'method':method,'horizon':int(h),'roundtrip_cost_bps':int(c),'year':int(yr),
    'return':float(eq[-1]-1),'drawdown':float((eq/np.maximum.accumulate(eq)-1).min()),'orders':int(g.orders.sum())})
 (OUT/'annual_results.json').write_text(json.dumps(annual,indent=2))
 print(json.dumps({'events':len(event_records),'saved':str(OUT)}),flush=True)

if __name__=='__main__':main()
