"""Disclosed post-result checks of market exposure, uncertainty and cost capacity."""
import analyze as a
import pandas as pd,numpy as np,json,math

events=pd.read_json(a.OUT/'rebound_events.json')
events['date']=events.date.astype(str)
frames={s:a.load(s,'5m')[0] for s in [s for g in a.GROUPS.values() for s in g]+['SPY']}
for i,e in events.iterrows():
    entry=pd.Timestamp(e.entry_time);exit=entry+pd.Timedelta(minutes=30)
    peer=[]
    for s in a.GROUPS[e.group]:
        if s!=e.symbol:
            f=frames[s];peer.append(f.loc[exit,'open']/f.loc[entry,'open']-1)
    events.loc[i,'peer_return']=float(np.mean(peer))
    events.loc[i,'excess_peer_return']=e.gross_trade_return-np.mean(peer)
    spy=frames['SPY']
    events.loc[i,'spy_return']=spy.loc[exit,'open']/spy.loc[entry,'open']-1
events.to_json(a.OUT/'rebound_enriched.json',orient='records',indent=2)
dates=sorted(set.intersection(*[set(f.date) for f in frames.values()]))[20:]
agg=events.groupby('date').agg(n=('gross_trade_return','size'),gross=('gross_trade_return','sum'),excess=('excess_peer_return','sum'))
agg=agg.reindex([str(d) for d in dates],fill_value=0)
rng=np.random.default_rng(81226);n=len(agg);reps=20000;block=5
starts=rng.integers(0,n,size=(reps,math.ceil(n/block)))
ix=((starts[:,:,None]+np.arange(block))%n).reshape(reps,-1)[:,:n]
counts=agg.n.values[ix].sum(axis=1)
gross=agg.gross.values[ix].sum(axis=1)/np.maximum(counts,1)
excess=agg.excess.values[ix].sum(axis=1)/np.maximum(counts,1)
rows=[]
for c in a.COSTS:
    rows.append({'cost_bps':c,'event_weighted_mean_net_bps':float((events.gross_trade_return-c/1e4).mean()*1e4),
        'event_weighted_net_ci95_bps':(np.quantile(gross[counts>0],[.025,.975])*1e4-c).tolist(),
        'peer_excess_net_mean_bps':float(events.excess_peer_return.mean()*1e4-c),
        'peer_excess_net_ci95_bps':(np.quantile(excess[counts>0],[.025,.975])*1e4-c).tolist()})
details={'uncertainty_method':'20000 circular five-session block resamples of all 39 screened sessions, preserve all events per day; ratio of total return sum to total event count; no multiple-test correction',
    'gross_mean_bps':float(events.gross_trade_return.mean()*1e4),'gross_sd_bps':float(events.gross_trade_return.std(ddof=1)*1e4),
    'peer_mean_bps':float(events.peer_return.mean()*1e4),'spy_mean_bps':float(events.spy_return.mean()*1e4),
    'max_events_day':int(events.groupby('date').size().max()),'unique_symbols':int(events.symbol.nunique()),
    'by_half':[],'cost_results':rows}
for name,mask in [('first_half',events.date<=str(dates[18])),('second_half',events.date>str(dates[18]))]:
    q=events[mask]
    details['by_half'].append({'split':name,'events':len(q),'gross_mean_bps':float(q.gross_trade_return.mean()*1e4),
        'net10_mean_bps':float(q.gross_trade_return.mean()*1e4-10),'peer_excess_gross_bps':float(q.excess_peer_return.mean()*1e4)})
details['by_group']=events.groupby('group').agg(events=('symbol','size'),gross_mean=('gross_trade_return','mean'),peer_excess=('excess_peer_return','mean')).reset_index().to_dict('records')
out={'rebound':details,'math':{'crypto_taker_roundtrip_breakeven':(1+.0095)/(1-.0095)-1,
    'fixed_data_cost_annual_by_capital':{str(e):99*12/e for e in [1000,2500,5000]},
    'n_independent_events_for_95pc_interval_at_5bps_net':(1.96*details['gross_sd_bps']/5)**2,
    'n_for_80pc_power_at_5bps_net':((1.96+.8416)*details['gross_sd_bps']/5)**2,
    'consecutive_losses_to_25pc':{str(r):math.ceil(math.log(.75)/math.log(1-r)) for r in [.0025,.005,.01,.02,.04]}}}
(a.OUT/'final_diagnostics.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
