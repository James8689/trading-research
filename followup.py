"""Research diagnostics and additional disclosed exploratory experiment, no trading."""
import analyze as a
import pandas as pd
import numpy as np
import json,math

def dump(name,value):
    (a.OUT/f'{name}.json').write_text(json.dumps(value,indent=2))

def closing_audit():
    rows=[]; overlaps=[]
    for base,bull,bear in [('QQQ','TQQQ','SQQQ'),('SPY','UPRO','SPXU')]:
        r=pd.read_json(a.OUT/f'closing_signals_{base}.json');r['date']=r.date.astype(str)
        lookup={}
        for s in [base,bull,bear]:
            f,_=a.load(s,'1h');lookup[s]={str(d):g for d,g in f.groupby('date')}
            small,_=a.load(s,'5m')
            for d,g in small.groupby('date'):
                if str(d) not in lookup[s]:continue
                h=lookup[s][str(d)].iloc[-1]
                b=g[g.minute>=930]
                overlaps.append({'symbol':s,'date':str(d),
                    'open_difference_bps':(h.open/b.iloc[0].open-1)*1e4,
                    'close_difference_bps':(h.close/b.iloc[-1].close-1)*1e4})
        r['etf_no_stop']=[lookup[x.instrument][x.date].iloc[-1].close/x.entry-1 for _,x in r.iterrows()]
        for name,mask in [('all',np.ones(len(r),bool)),('strong',r.strong),('strong_agree',r.strong&r.agreement)]:
            q=r[mask]
            rows.append({'base':base,'variant':name,'trades':len(q),'stop_fraction':float(q.stopped.mean()),
                'underlying_signed_mean_bps':float(q.signed_underlying_return.mean()*1e4),
                'actual_etf_no_stop_mean_bps':float(q.etf_no_stop.mean()*1e4),
                'actual_etf_stopped_mean_bps':float(q.gross_trade_return.mean()*1e4),
                'underlying_mean_ci95_bps':[v*1e4 for v in a.block_ci(q.signed_underlying_return)]})
    dump('closing_audit',rows);dump('overlap_audit',overlaps)
    print('CLOSING AUDIT',json.dumps(rows))
    o=pd.DataFrame(overlaps)
    print('OVERLAP',o[['open_difference_bps','close_difference_bps']].abs().describe().to_string())

def rebound_fast(fs):
    dates=sorted(set.intersection(*[set(f.date) for f in fs.values()]))[20:]
    look={s:{d:g for d,g in f.groupby('date')} for s,f in fs.items()}
    events=[]
    for group,names in a.GROUPS.items():
        names=[s for s in names if s in fs]
        if len(names)<4:continue
        for date in dates:
            bars=[look[s][date] for s in names]
            close=np.column_stack([b.close.values for b in bars])
            for si,s in enumerate(names):
                others=[i for i in range(len(names)) if i!=si];cooldown=-1
                for k in range(6,60):
                    if k<cooldown:continue
                    start=k-5;bottom=k-2
                    selloff=close[bottom,others]/close[start,others]-1
                    peer_drop=float(np.median(selloff));stock_drop=close[bottom,si]/close[start,si]-1
                    if not(peer_drop<=-.003 and (selloff<0).mean()>=.7 and stock_drop<0):continue
                    recovery=float(np.median(close[k,others]/close[bottom,others]-1))
                    if recovery<-.5*peer_drop:continue
                    stock_recovery=close[k,si]/close[bottom,si]-1;residual=recovery-stock_recovery
                    if residual<.003 or close[k,si]<=close[k-1,si]:continue
                    f=bars[si];entry=float(f.iloc[k+1].open);exit=float(f.iloc[k+7].open)
                    events.append({'date':str(date),'group':group,'symbol':s,'entry_time':str(f.index[k+1]),
                        'peer_drop':peer_drop,'recovery':recovery,'residual':float(residual),
                        'entry':entry,'exit':exit,'gross_trade_return':exit/entry-1})
                    cooldown=k+8
    dump('rebound_events',events);rows=[]
    r=pd.DataFrame(events)
    if len(r):
        for c in a.COSTS:
            net=r.gross_trade_return-c/1e4;days=r.assign(net=net).groupby('date').net.mean()
            rows.append({'cost_bps':c,'events':len(r),'event_days':len(days),'sessions_screened':len(dates),
                'start':str(dates[0]),'end':str(dates[-1]),'gross_avg_trade_bps':float(r.gross_trade_return.mean()*1e4),
                'net_avg_trade_bps':float(net.mean()*1e4),'net_positive_fraction':float((net>0).mean()),
                'event_day_mean_ci95':a.block_ci(days)})
    dump('rebound_results',rows);print('REBOUND',json.dumps(rows))

def index_opening():
    frames={s:a.load(s,'5m')[0] for s in ['QQQ','TQQQ','SQQQ']}
    look={s:{d:g for d,g in f.groupby('date')} for s,f in frames.items()}
    dates=sorted(set.intersection(*[set(v) for v in look.values()]))[20:]
    ov=frames['QQQ'].groupby('date').volume.first()
    rv=ov/ov.rolling(14,min_periods=14).mean().shift(1)
    records=[]
    for d in dates:
        q=look['QQQ'][d].iloc[0]
        symbol='TQQQ' if q.close>q.open else 'SQQQ'
        if q.close==q.open:continue
        f=look[symbol][d];entry=float(f.iloc[1].open);stop=float(f.iloc[0].low)
        if stop>=entry:continue
        reason='time';exit=float(f[f.minute==955].iloc[0].open)
        for _,bar in f.iloc[1:].iterrows():
            if bar.minute>=955:break
            if bar.low<=stop:exit=min(float(bar.open),stop);reason='stop';break
        records.append({'date':str(d),'symbol':symbol,'rvol':float(rv.loc[d]),'entry':entry,'stop':stop,
            'exit':exit,'gross_trade_return':exit/entry-1,'risk_width':(entry-stop)/entry,'reason':reason})
    r=pd.DataFrame(records);results=[];curves=[]
    for name,threshold in [('all',0),('rvol1.5',1.5)]:
        for cost in a.COSTS:
            eq=2500.;curve=[];selected=[]
            bydate={x['date']:x for x in records if x['rvol']>=threshold}
            for d in dates:
                x=bydate.get(str(d));n=0;ret=0
                if x:
                    n=math.floor(min(eq*.5/x['entry'],eq*.005/(x['entry']-x['stop']+x['entry']*cost/1e4)))
                    ret=n*x['entry']/eq*(x['gross_trade_return']-cost/1e4)
                    if n>0:selected.append(x)
                eq*=1+ret
                curve.append({'date':str(d),'variant':name,'cost_bps':cost,'trades':int(n>0),'account_return':ret,'equity':eq})
            cr=pd.DataFrame(curve);ex=pd.DataFrame(selected)
            for split,mask in [('all',np.ones(len(cr),bool)),('first_half',np.arange(len(cr))<len(cr)//2),('second_half',np.arange(len(cr))>=len(cr)//2)]:
                part=cr[mask];sel=ex[ex.date.isin(part.date)]
                m=a.performance(part.account_return)
                m.update({'variant':name,'cost_bps':cost,'split':split,'trades':int(part.trades.sum()),
                    'gross_avg_trade_bps':float(sel.gross_trade_return.mean()*1e4) if len(sel) else None,
                    'net_win_fraction':float((sel.gross_trade_return>cost/1e4).mean()) if len(sel) else None,
                    'mean_daily_ci95':a.block_ci(part.account_return),'start':part.date.iloc[0],'end':part.date.iloc[-1]})
                results.append(m)
            curves.extend(curve)
    dump('index_opening_trades',records);dump('index_opening_results',results);dump('index_opening_daily',curves)
    print('INDEX OPENING AT 10 BPS',pd.DataFrame(results).query('cost_bps==10').to_string(index=False))

if __name__=='__main__':
    a.closing()
    closing_audit()
    fs,ds=a.stock_setup()
    a.opening(fs,ds,True)
    rebound_fast(fs)
    index_opening()
    dump('data_audit',a.AUDIT)
