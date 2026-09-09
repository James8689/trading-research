"""Research-only historical experiments. No accounts, credentials, or order submission."""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'analysis'
OUT.mkdir(exist_ok=True)
PLAN = json.loads((ROOT/'experiment_plan.json').read_text())
GROUPS = json.loads((ROOT/'groups.json').read_text())
CUTOFF = pd.Timestamp(PLAN['cutoff_exclusive']).date()
COSTS = [0,5,10,20]
AUDIT=[]

def load(symbol, interval, complete_only=True):
    path=ROOT/'raw'/f'{symbol}_{interval}.json'
    j=json.loads(path.read_text())['chart']['result'][0]
    if j['meta'].get('dataGranularity') != interval:
        raise ValueError(f'Wrong provider interval for {symbol}: {j["meta"].get("dataGranularity")} != {interval}')
    ix=pd.to_datetime(j['timestamp'],unit='s',utc=True).tz_convert('America/New_York')
    df=pd.DataFrame(j['indicators']['quote'][0],index=ix).sort_index()
    original=len(df)
    df=df.loc[~df.index.duplicated(keep='last')]
    df=df[(df.index.date<CUTOFF)&(df.index.dayofweek<5)]
    minutes=df.index.hour*60+df.index.minute
    df=df[(minutes>=570)&(minutes<960)]
    bad=df[['open','high','low','close']].isna().any(axis=1)
    bad|=(df[['open','high','low','close']]<=0).any(axis=1)
    bad|=(df['low']>df[['open','close','high']].min(axis=1)+1e-6)
    bad|=(df['high']<df[['open','close','low']].max(axis=1)-1e-6)
    bad|=(df['volume']<0)|df['volume'].isna()
    bad_count=int(bad.sum())
    df=df[~bad]
    df['date']=df.index.date
    df['minute']=df.index.hour*60+df.index.minute
    expected=list(range(570,960,5 if interval=='5m' else 60))
    complete=[d for d,g in df.groupby('date') if g.minute.tolist()==expected]
    if complete_only:df=df[df.date.isin(complete)]
    AUDIT.append({'symbol':symbol,'interval':interval,'original_rows':original,
                  'used_rows':len(df),'complete_sessions':len(complete),'invalid_bars':bad_count,
                  'first':str(df.index.min()),'last':str(df.index.max()),
                  'provider_granularity':j['meta'].get('dataGranularity')})
    return df,j

def daily(df):
    return df.groupby('date').agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),volume=('volume','sum'))

def performance(rets):
    r=np.asarray(rets,dtype=float)
    if len(r)==0:return {}
    eq=np.r_[1.,np.cumprod(1+r)]
    dd=eq/np.maximum.accumulate(eq)-1
    sd=r.std(ddof=1) if len(r)>1 else 0
    return {'sessions':len(r),'total_return':eq[-1]-1,'cagr':eq[-1]**(252/len(r))-1,
            'annual_vol':sd*np.sqrt(252),'sharpe_zero_cash':r.mean()/sd*np.sqrt(252) if sd else 0,
            'close_to_close_max_drawdown':float(dd.min()),'worst_day':float(r.min()),
            'positive_days':float((r>0).mean()),'mean_daily':float(r.mean())}

def block_ci(x, reps=5000, block=5, seed=71026):
    x=np.asarray(x,float);n=len(x)
    if n<5:return [None,None]
    rng=np.random.default_rng(seed)
    start=rng.integers(0,n,size=(reps,math.ceil(n/block)))
    ix=(start[:,:,None]+np.arange(block))%n
    means=x[ix.reshape(reps,-1)[:,:n]].mean(axis=1)
    return np.quantile(means,[.025,.975]).tolist()

def closing():
    allresults=[]; allrows=[]
    for base,bull,bear in [('QQQ','TQQQ','SQQQ'),('SPY','UPRO','SPXU')]:
        frames={};meta={}
        for s in [base,bull,bear]:frames[s],meta[s]=load(s,'1h')
        # Keep early-close sessions in previous-close and volatility history,
        # while requiring full sessions for actual closing-time trades.
        history,_=load(base,'1h',complete_only=False)
        dm=daily(history)
        dm['prev']=dm.close.shift(1)
        divs=meta[base].get('events',{}).get('dividends',{})
        for event in divs.values():
            day=pd.Timestamp(event['date'],unit='s',tz='UTC').tz_convert('America/New_York').date()
            if day in dm.index:dm.loc[day,'prev']-=event['amount']
        dm['vol']=(dm.close/dm['prev']-1).rolling(20,min_periods=20).std().shift(1)
        lookup={s:{d:g for d,g in f.groupby('date')} for s,f in frames.items()}
        records=[]
        for d,row in dm.dropna().iterrows():
            if any(d not in lookup[s] for s in [base,bull,bear]):continue
            b=lookup[base][d]
            signal=b.loc[b.minute==870,'close'].iloc[0]/row['prev']-1
            daytime=b.loc[b.minute==870,'close'].iloc[0]/b.iloc[0].open-1
            direction=1 if signal>0 else -1
            ex=bull if direction>0 else bear
            bar=lookup[ex][d].loc[lambda z:z.minute==930].iloc[0]
            entry=float(bar.open)
            exit=float(bar.close)
            stopped=bool(bar.low<=entry*.99)
            if stopped:exit=entry*.99
            gross=exit/entry-1
            raw_underlying=b.iloc[-1]['close']/b.iloc[-1]['open']-1
            records.append({'date':str(d),'base':base,'instrument':ex,'signal':signal,'daily_vol':row.vol,
                            'daytime':daytime,'strong':abs(signal)>=.75*row.vol,
                            'agreement':signal*daytime>0,'entry':entry,'exit':exit,'stopped':stopped,
                            'gross_trade_return':gross,'signed_underlying_return':direction*raw_underlying,
                            'passive_underlying_return':row['close']/row['prev']-1})
        rec=pd.DataFrame(records)
        for name,mask in [('all',np.ones(len(rec),bool)),('strong',rec.strong.values),('strong_agree',(rec.strong&rec.agreement).values)]:
            for cost in COSTS:
                curve=[];equity=2500.;rets=[];n=0;notional=[]
                for i,x in rec.iterrows():
                    if mask[i]:
                        shares=math.floor(.5*equity/x.entry)
                        weight=shares*x.entry/equity
                        r=weight*(x.gross_trade_return-cost/1e4)
                        n+=int(shares>0);notional.append(weight)
                    else:r=0.;weight=0.;shares=0
                    equity*=1+r;rets.append(r)
                    curve.append({'date':x.date,'base':base,'variant':name,'cost_bps':cost,'active':bool(mask[i]),
                                  'instrument':x.instrument,'shares':shares,'weight':weight,'account_return':r,'equity':equity,
                                  'gross_trade_return':x.gross_trade_return,'entry':x.entry,'exit':x.exit,'stopped':bool(x.stopped)})
                frame=pd.DataFrame(curve)
                for split,smask in [('all',np.ones(len(frame),bool)),('through_2024',frame.date<'2025-01-01'),('2025',frame.date.str.startswith('2025')),('2026',frame.date.str.startswith('2026'))]:
                    part=frame[smask]
                    if not len(part):continue
                    selected=rec.loc[smask].loc[lambda z:part.active.values]
                    metrics=performance(part.account_return)
                    metrics.update({'base':base,'variant':name,'cost_bps':cost,'split':split,'trades':int(part.shares.gt(0).sum()),
                        'trade_win_rate_net':float((selected.gross_trade_return>cost/1e4).mean()) if len(selected) else None,
                        'gross_avg_trade_bps':float(selected.gross_trade_return.mean()*1e4) if len(selected) else None,
                        'mean_daily_ci95':block_ci(part.account_return),'start':part.date.iloc[0],'end':part.date.iloc[-1]})
                    allresults.append(metrics)
                allrows.extend(curve)
        rec.to_json(OUT/f'closing_signals_{base}.json',orient='records',indent=2)
    (OUT/'closing_results.json').write_text(json.dumps(allresults,indent=2))
    (OUT/'closing_daily.json').write_text(json.dumps(allrows,indent=2))
    print('CLOSING AT 5 BPS')
    print(pd.DataFrame(allresults).query('cost_bps==5')[['base','variant','split','trades','total_return','cagr','close_to_close_max_drawdown','gross_avg_trade_bps']].round(4).to_string(index=False))

def stock_setup():
    fs={}; ds={}
    for s in [x for v in GROUPS.values() for x in v]:
        if not (ROOT/'raw'/f'{s}_5m.json').exists():continue
        f,_=load(s,'5m');fs[s]=f
        d=daily(f)
        prior=d.close.shift(1)
        tr=pd.concat([d.high-d.low,(d.high-prior).abs(),(d.low-prior).abs()],axis=1).max(axis=1)
        d['atr']=tr.rolling(14,min_periods=14).mean().shift(1)
        d['avg_vol']=d.volume.rolling(14,min_periods=14).mean().shift(1)
        d['opening_volume']=f.groupby('date').volume.first()
        d['rvol']=d.opening_volume/d.opening_volume.rolling(14,min_periods=14).mean().shift(1)
        ds[s]=d
    return fs,ds

def opening(fs,ds,favorable_chronology=False):
    dates=sorted(set.intersection(*[set(d.index) for d in ds.values()]))[20:]
    look={s:{d:g for d,g in f.groupby('date')} for s,f in fs.items()}
    orders=[]
    for date in dates:
        for s in fs:
            if date not in look[s]:continue
            d=ds[s].loc[date];f=look[s][date];first=f.iloc[0]
            if not (first.close>first.open and first.open>5 and d.avg_vol>=1e6 and d.atr>.5):continue
            trigger=float(first.high+.01);entered=False
            for ix,bar in f.iloc[1:].iterrows():
                if not entered:
                    if bar.minute>=660:break
                    if bar.high<trigger:continue
                    entry=max(float(bar.open),trigger);stop=entry-.1*float(d.atr);entered=True;entry_time=ix
                    ambiguous=bool(bar.low<=stop and bar.open<trigger)
                if bar.minute>=955:
                    exit=float(bar.open);reason='time';break
                entry_bar_ambiguous=(ix==entry_time and ambiguous and bar.close>stop)
                if bar.low<=stop and not (favorable_chronology and entry_bar_ambiguous):
                    exit=min(float(bar.open),stop) if ix!=entry_time else stop
                    reason='stop';break
            else:
                if entered:exit=float(f.iloc[-1].close);reason='close'
            if entered:
                orders.append({'date':str(date),'symbol':s,'rvol':float(d.rvol),'entry':entry,'exit':exit,
                  'stop':stop,'risk_width':(entry-stop)/entry,'gross_trade_return':exit/entry-1,
                  'entry_time':str(entry_time),'reason':reason,'same_bar_ambiguous':ambiguous})
    trades=pd.DataFrame(orders)
    results=[];curve_rows=[]
    for name,threshold,limit in [('rvol1.5_top3',1.5,3),('rvol1.0_top3',1.,3),('all_positive',0.,None)]:
        # Rank eligible candidates at 09:35, including candidates that never trigger.
        chosen={}
        for date in dates:
            candidates=[]
            for s in fs:
                if date not in look[s]:continue
                d=ds[s].loc[date];first=look[s][date].iloc[0]
                if first.close>first.open and first.open>5 and d.avg_vol>=1e6 and d.atr>.5 and d.rvol>=threshold:
                    candidates.append((s,float(d.rvol)))
            candidates=sorted(candidates,key=lambda x:(-x[1],x[0]))
            chosen[str(date)]=set(s for s,_ in (candidates[:limit] if limit else candidates))
        for cost in COSTS:
            eq=2500.;rows=[];executed=[]
            for date in dates:
                key=str(date);candidate_names=chosen[key]
                subset=trades[(trades.date==key)&trades.symbol.isin(candidate_names)] if len(trades) else trades
                cap=(1/3) if limit else 1/max(len(candidate_names),1)
                pnl=0.;active=0;weights=0
                for _,t in subset.iterrows():
                    cost_per_share=t.entry*cost/1e4
                    shares=math.floor(min(eq*cap/t.entry,eq*.0025/(t.entry-t.stop+cost_per_share)))
                    if shares<=0:continue
                    weight=shares*t.entry/eq
                    pnl+=shares*(t.exit-t.entry-cost_per_share);active+=1;weights+=weight
                    executed.append(dict(t,variant=name,cost_bps=cost,shares=shares,net_trade_return=t.gross_trade_return-cost/1e4))
                ret=pnl/eq;eq+=pnl
                rows.append({'date':key,'variant':name,'cost_bps':cost,'account_return':ret,'equity':eq,'trades':active,'gross_weight':weights})
            frame=pd.DataFrame(rows);ex=pd.DataFrame(executed)
            for split,smask in [('all',np.ones(len(frame),bool)),('first_half',np.arange(len(frame))<len(frame)//2),('second_half',np.arange(len(frame))>=len(frame)//2)]:
                part=frame[smask];sel=ex[ex.date.isin(part.date)] if len(ex) else ex
                metrics=performance(part.account_return)
                metrics.update({'variant':name,'cost_bps':cost,'split':split,'trades':int(part.trades.sum()),
                    'gross_avg_trade_bps':float(sel.gross_trade_return.mean()*1e4) if len(sel) else None,
                    'trade_win_rate_net':float((sel.net_trade_return>0).mean()) if len(sel) else None,
                    'same_bar_ambiguous':int(sel.same_bar_ambiguous.sum()) if len(sel) else 0,
                    'mean_daily_ci95':block_ci(part.account_return),'start':part.date.iloc[0],'end':part.date.iloc[-1]})
                results.append(metrics)
            curve_rows.extend(rows)
    prefix='opening_favorable' if favorable_chronology else 'opening'
    trades.to_json(OUT/f'{prefix}_all_trades.json',orient='records',indent=2)
    (OUT/f'{prefix}_results.json').write_text(json.dumps(results,indent=2))
    (OUT/f'{prefix}_daily.json').write_text(json.dumps(curve_rows,indent=2))
    print('OPENING AT 10 BPS')
    print(pd.DataFrame(results).query('cost_bps==10')[['variant','split','trades','total_return','close_to_close_max_drawdown','gross_avg_trade_bps','trade_win_rate_net','same_bar_ambiguous']].round(4).to_string(index=False))

def rebound(fs):
    events=[]
    dates=sorted(set.intersection(*[set(f.date) for f in fs.values()]))[20:]
    for group,names in GROUPS.items():
        names=[s for s in names if s in fs]
        if len(names)<4:continue
        for date in dates:
            bars={s:fs[s][fs[s].date==date] for s in names}
            if any(len(x)!=78 for x in bars.values()):continue
            close=pd.DataFrame({s:x.close.values for s,x in bars.items()})
            for s in names:
                others=[n for n in names if n!=s]
                cooldown=-1
                for k in range(6,60):
                    if k<cooldown:continue
                    a=k-5;b=k-2
                    selloff=close.loc[b,others]/close.loc[a,others]-1
                    peer_drop=float(selloff.median())
                    stock_drop=close.loc[b,s]/close.loc[a,s]-1
                    if not (peer_drop<=-.003 and (selloff<0).mean()>=.7 and stock_drop<0):continue
                    recovery=float((close.loc[k,others]/close.loc[b,others]-1).median())
                    if recovery<-.5*peer_drop:continue
                    stock_recovery=close.loc[k,s]/close.loc[b,s]-1
                    residual=recovery-stock_recovery
                    if residual<.003 or close.loc[k,s]<=close.loc[k-1,s]:continue
                    f=bars[s];entry=float(f.iloc[k+1].open);exit=float(f.iloc[k+7].open)
                    events.append({'date':str(date),'group':group,'symbol':s,'entry_time':str(f.index[k+1]),
                        'peer_drop':peer_drop,'recovery':recovery,'residual':float(residual),'entry':entry,'exit':exit,
                        'gross_trade_return':exit/entry-1})
                    cooldown=k+8
    frame=pd.DataFrame(events)
    frame.to_json(OUT/'rebound_events.json',orient='records',indent=2)
    results=[]
    if len(frame):
        for cost in COSTS:
            net=frame.gross_trade_return-cost/1e4
            daymean=frame.assign(net=net).groupby('date').net.mean()
            results.append({'cost_bps':cost,'events':len(frame),'event_days':len(daymean),
                'gross_avg_trade_bps':float(frame.gross_trade_return.mean()*1e4),'net_avg_trade_bps':float(net.mean()*1e4),
                'net_positive_fraction':float((net>0).mean()),'event_day_mean_ci95':block_ci(daymean)})
    (OUT/'rebound_results.json').write_text(json.dumps(results,indent=2))
    print('REBOUND',json.dumps(results))

if __name__=='__main__':
    closing()
    fs,ds=stock_setup()
    opening(fs,ds)
    rebound(fs)
    (OUT/'data_audit.json').write_text(json.dumps(AUDIT,indent=2))
