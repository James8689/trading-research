"""Exploratory finite-capital replay of rebound signals; cannot submit orders."""
import analyze as a
import pandas as pd,numpy as np,json,math
events=json.loads((a.OUT/'rebound_events.json').read_text())
frames={s:a.load(s,'5m')[0] for s in {e['symbol'] for e in events}}
for e in events:
    e['entry_ts']=pd.Timestamp(e['entry_time']);e['time_exit']=e['entry_ts']+pd.Timedelta(minutes=30)
    f=frames[e['symbol']];past=f[(f.index<e['entry_ts'])&(f.index>=e['entry_ts']-pd.Timedelta(minutes=25))]
    assert len(past)==5
    e['stop']=float(past.low.min()-.01);e['exit_ts']=e['time_exit'];e['reason']='time'
    for ix,bar in f[(f.index>=e['entry_ts'])&(f.index<e['time_exit'])].iterrows():
        if bar.low<=e['stop']:
            e['exit']=min(float(bar.open),e['stop']);e['exit_ts']=ix+pd.Timedelta(minutes=5);e['reason']='stop';break
    e['gross_trade_return']=e['exit']/e['entry']-1
events.sort(key=lambda e:(e['entry_ts'],-e['residual'],e['symbol']))
dates=sorted({str(d) for d in next(iter(frames.values())).date})[20:]
summary=[];alltrades=[];curves=[]
for cost in a.COSTS:
    equity=2500.;active=[];trades=[];curve=[];counts={}
    def settle(until):
        global equity,active
        done=[t for t in active if t['exit_ts']<=until]
        for t in sorted(done,key=lambda t:t['exit_ts']):equity+=t['pnl']
        active=[t for t in active if t['exit_ts']>until]
    for date in dates:
        before=equity;n=0
        for e in [e for e in events if e['date']==date]:
            settle(e['entry_ts'])
            if len(active)>=2 or e['group'] in {t['group'] for t in active}:continue
            if e['stop']>=e['entry']:continue
            dollars_at_risk=e['entry']-e['stop']+e['entry']*cost/1e4
            shares=math.floor(min(equity*.25/e['entry'],equity*.0025/dollars_at_risk))
            if shares<=0:continue
            t=dict(e,cost_bps=cost,shares=shares,pnl=shares*(e['exit']-e['entry']-e['entry']*cost/1e4))
            active.append(t);trades.append(t);n+=1
        settle(pd.Timestamp(date+' 16:00',tz='America/New_York'))
        assert not active
        curve.append({'date':date,'cost_bps':cost,'trades':n,'equity':equity,'account_return':equity/before-1})
    r=pd.DataFrame(curve);t=pd.DataFrame(trades);m=a.performance(r.account_return)
    m.update({'cost_bps':cost,'trades':len(t),'active_days':int(r.trades.gt(0).sum()),'stops':int(t.reason.eq('stop').sum()),
        'net_win_fraction':float(t.pnl.gt(0).mean()),'mean_daily_ci95':a.block_ci(r.account_return),
        'start':dates[0],'end':dates[-1],'ending_equity':equity,'mean_notional':float((t.shares*t.entry).mean())})
    summary.append(m);curves.extend(curve)
    for q in trades:
        alltrades.append({k:(str(v) if isinstance(v,pd.Timestamp) else v) for k,v in q.items()})
for name,v in [('rebound_portfolio_results',summary),('rebound_portfolio_daily',curves),('rebound_portfolio_trades',alltrades)]:
    (a.OUT/f'{name}.json').write_text(json.dumps(v,indent=2))
print(json.dumps(summary,indent=2))
