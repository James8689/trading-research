"""Frozen daily-history experiments. No brokerage credentials or order submission."""
from pathlib import Path
import json,math
import pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'daily_results';OUT.mkdir(exist_ok=True)
COSTS=[0,2,5,10];AUDIT=[]
def load(s):
 j=json.loads((ROOT/'daily_raw'/f'{s}.json').read_text())['chart']['result'][0]
 assert j['meta']['dataGranularity']=='1d'
 ix=pd.to_datetime(j['timestamp'],unit='s',utc=True).tz_convert('America/New_York').normalize().tz_localize(None)
 f=pd.DataFrame(j['indicators']['quote'][0],index=ix)
 f['adjusted']=j['indicators']['adjclose'][0]['adjclose']
 bad=f[['open','high','low','close','adjusted']].isna().any(axis=1)
 bad|=(f[['open','high','low','close','adjusted']]<=0).any(axis=1)
 bad|=(f.low>f[['open','close']].min(axis=1)+1e-5)|(f.high<f[['open','close']].max(axis=1)-1e-5)
 if bad.sum():raise ValueError(f'{s}: {bad.sum()} bad daily bars; inspect before using')
 f['split']=1.;f['future_split']=1.;f['dividend']=0.
 for e in j.get('events',{}).get('splits',{}).values():
  d=pd.Timestamp(e['date'],unit='s',tz='UTC').tz_convert('America/New_York').tz_localize(None).normalize();r=float(e['numerator'])/float(e['denominator'])
  if d in f.index:f.loc[d,'split']*=r
  f.loc[f.index<d,'future_split']*=r
 for e in j.get('events',{}).get('dividends',{}).values():
  d=pd.Timestamp(e['date'],unit='s',tz='UTC').tz_convert('America/New_York').tz_localize(None).normalize()
  if d in f.index:f.loc[d,'dividend']+=float(e['amount'])*f.loc[d,'future_split']
 for col in ['open','high','low','close']:f[col]*=f.future_split
 f['cash_total_return']=(f.close+f.dividend)*f.split/f.close.shift(1)-1
 discrepancy=(f.cash_total_return-(f.adjusted/f.adjusted.shift(1)-1)).abs()
 AUDIT.append({'symbol':s,'rows':len(f),'start':str(f.index[0].date()),'end':str(f.index[-1].date()),
  'split_events':len(j.get('events',{}).get('splits',{})),'max_dividend_return_difference_bps':float(discrepancy.max()*1e4),
  'mean_dividend_return_difference_bps':float(discrepancy.mean()*1e4),
  'largest_abs_return':float(f.cash_total_return.abs().max()),'nominal_first_close':float(f.close.iloc[0])})
 return f
def stats(rows):
 f=pd.DataFrame(rows);r=f.account_return.to_numpy();eq=np.r_[1,np.cumprod(1+r)];n=len(r)
 sd=r.std(ddof=1)
 rng=np.random.default_rng(991122);starts=rng.integers(0,n,size=(3000,math.ceil(n/5)))
 indexes=((starts[:,:,None]+np.arange(5))%n).reshape(3000,-1)[:,:n]
 ci=np.quantile(r[indexes].mean(axis=1),[.025,.975])
 return {'sessions':n,'total_return':float(eq[-1]-1),'cagr':float(eq[-1]**(252/n)-1),
  'eod_max_drawdown':float((eq/np.maximum.accumulate(eq)-1).min()),'annual_vol':float(sd*np.sqrt(252)),
  'sharpe_zero_cash':float(r.mean()/sd*np.sqrt(252)) if sd else 0.,'worst_day':float(r.min()),
  'positive_day_fraction':float((r>0).mean()),'mean_daily_ci95':ci.tolist(),
  'orders':int(f.orders.sum()),'roundtrip_equivalent':float(f.orders.sum()/2),
  'mean_weight':float(f.weight.mean()),'fees':float(f.fee.sum()),'ending_equity':float(f.equity.iloc[-1])}
FRAMES={s:load(s) for s in ['SPY','QQQ','SSO','QLD']}
assert all(FRAMES[s].index.equals(FRAMES['SPY'].index) for s in FRAMES)
for s in ['SPY','QQQ']:
 f=FRAMES[s];f['trend']=(f.adjusted>f.adjusted.rolling(200,min_periods=200).mean()).shift(1).fillna(False)
for s in ['SSO','QLD']:
 f=FRAMES[s];f['vol']=(f.adjusted/f.adjusted.shift(1)-1).rolling(60,min_periods=60).std().shift(1)*np.sqrt(252)
def run(base,etf,method,cost,start,end):
 f=FRAMES[etf];b=FRAMES[base];indices=np.where((f.index>=pd.Timestamp(start))&(f.index<=pd.Timestamp(end)))[0]
 cash=2500.;shares=0.;equity=2500.;rows=[];state=False
 for k,i in enumerate(indices):
  day=f.index[i];bar=f.iloc[i];prev_equity=equity;fee=0.;orders=0;weight=0.
  if method=='buy_hold':
   first=f.iloc[indices[0]]
   adjusted_entry=first.adjusted*first.open/first.close
   equity=2500./(1+cost/20000)*bar.adjusted/adjusted_entry
   fee=2500./(1+cost/20000)*(cost/20000) if k==0 else 0.
   orders=int(k==0);weight=1.
   if k==len(indices)-1:
    exitfee=equity*cost/20000;equity-=exitfee;fee+=exitfee;orders+=1
  elif method.startswith('overnight'):
   if k>0:
    entry=f.iloc[i-1];signal=bool(b.iloc[i-1].trend) if method=='overnight_trend' else True
    if signal:
     qty=math.floor(.5*equity/(entry.close*(1+cost/20000)))
     notional=qty*entry.close;outqty=qty*bar.split
     exitnotional=outqty*bar.open
     fee=(notional+exitnotional)*cost/20000
     equity+=exitnotional+outqty*bar.dividend-notional-fee
     orders=2 if qty>0 else 0;weight=notional/prev_equity
   cash=equity
  else:
   if k>0:
    shares*=bar.split;cash+=shares*bar.dividend
   open_equity=cash+shares*bar.open
   signal=True if method=='buy_hold' else bool(b.iloc[i].trend)
   month_change=k==0 or day.month!=f.index[indices[k-1]].month
   rebalance=k==0 or signal!=state or (method=='trend_vol18' and month_change)
   if rebalance:
    w=1. if method=='buy_hold' else (.5 if method=='trend_fixed50' else min(1.,.18/bar.vol))
    w=w if signal else 0.
    target=math.floor(w*open_equity/(bar.open*(1+cost/20000)))
    delta=target-shares
    if delta>0:delta=min(delta,math.floor(cash/(bar.open*(1+cost/20000))))
    fee=abs(delta)*bar.open*cost/20000;cash-=delta*bar.open+fee;shares+=delta
    orders=int(delta!=0);state=signal
   assert cash>=-1e-7
   weight=shares*bar.open/(cash+shares*bar.open) if cash+shares*bar.open else 0
   equity=cash+shares*bar.close
   if k==len(indices)-1 and shares>0:
    exitfee=shares*bar.close*cost/20000;equity-=exitfee;fee+=exitfee;orders+=1;cash=equity;shares=0
  rows.append({'date':str(day.date()),'base':base,'etf':etf,'method':method,'roundtrip_cost_bps':cost,
   'equity':float(equity),'account_return':float(equity/prev_equity-1),'orders':orders,'weight':float(weight),'fee':float(fee)})
 return rows
def main():
 results=[];curves=[]
 for split,start,end in [('all','2011-01-01','2025-12-31'),('development','2011-01-01','2021-12-31'),('reserved','2022-01-01','2025-12-31')]:
  for base,etf in [('SPY','SSO'),('QQQ','QLD')]:
   for method in ['overnight_always','overnight_trend','trend_fixed50','trend_vol18','buy_hold']:
    instrument=base if method=='buy_hold' else etf
    for cost in COSTS:
     rows=run(base,instrument,method,cost,start,end)
     result=stats(rows);result.update(split=split,base=base,etf=instrument,method=method,roundtrip_cost_bps=cost,
       start=rows[0]['date'],end=rows[-1]['date'])
     results.append(result)
     if split=='all':curves.extend(rows)
     if split=='reserved' and cost==5:print(json.dumps(result),flush=True)
 (OUT/'results.json').write_text(json.dumps(results,indent=2))
 (OUT/'daily_curves.json').write_text(json.dumps(curves,indent=2))
 (OUT/'data_audit.json').write_text(json.dumps(AUDIT,indent=2))
 annual=[]
 df=pd.DataFrame(curves)
 for (base,method,cost,year),g in df.groupby(['base','method','roundtrip_cost_bps',df.date.str[:4]]):
  r=g.account_return.to_numpy();eq=np.r_[1,np.cumprod(1+r)]
  annual.append({'base':base,'method':method,'roundtrip_cost_bps':int(cost),'year':int(year),
   'total_return':float(eq[-1]-1),'drawdown':float((eq/np.maximum.accumulate(eq)-1).min()),'orders':int(g.orders.sum())})
 (OUT/'annual_results.json').write_text(json.dumps(annual,indent=2))
 print('AUDIT',json.dumps(AUDIT),flush=True)

if __name__=="__main__":main()
