"""Build the research memo and reusable chart data. This does not trade."""
from pathlib import Path
import json,math
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import ImageReader
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'deliverables'; OUT.mkdir(exist_ok=True)
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
read=lambda n:json.loads((ROOT/'analysis'/f'{n}.json').read_text())
diag=read('final_diagnostics');rb=diag['rebound'];portfolio=read('rebound_portfolio_results')
sources=[
 ('Yahoo Finance chart service','Primary input data for our calculations: 43 symbols at five-minute resolution and six ETFs at hourly resolution; retrieved September 8, 2026. The saved manifest contains every query URL and SHA-256 hash. This is vendor OHLCV data, not verified executable quotes.','https://query1.finance.yahoo.com/v8/finance/chart/QQQ?range=730d&interval=1h'),
 ('Zarattini, Barbon and Aziz, A Profitable Day Trading Strategy for the U.S. Equity Market','2024 paper, Tables 1-3; long and short stock opening breakouts, volume selection and sensitivity.','https://concretumgroup.com/wp-content/uploads/2026/02/A-Profitable-Day-Trading-Strategy-For-The-U.S.-Equity-Market.pdf'),
 ('Zarattini and Aziz, Can Day Trading Really Be Profitable?','2023 paper; QQQ/TQQQ opening-direction strategy and explicit no-slippage assumption.','https://concretumgroup.com/wp-content/uploads/2026/02/Can-Day-Trading-Really-Be-Profitable.pdf'),
 ('QuantConnect, Opening Range Breakout for Stocks in Play','Independent implementation published December 2024; the displayed research test covers 2016.','https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/'),
 ('Baltussen, Da, Lammers and Martens, Hedging Demand and Market Intraday Momentum','Journal of Financial Economics 142(1), 2021, 377-403; author institution record.','https://pure.eur.nl/en/publications/hedging-demand-and-market-intraday-momentum/'),
 ('Robinhood Crypto fee schedule','Schedule dated June 22, 2026; entry-tier maker/taker rates.','https://cdn.robinhood.com/assets/robinhood/legal/rhc-fee-schedule.pdf'),
 ('Robinhood, Crypto fee tiers','API v2 taker-fee treatment during maker/taker rollout; account pricing needs verification.','https://robinhood.com/us/en/support/articles/crypto-fee-tiers/'),
 ('Robinhood, Trading with your agent','Supported instruments, equity tools, limited margin and settlement.','https://robinhood.com/us/en/support/articles/trading-with-your-agent/'),
 ('Robinhood, Day trading','June 4, 2026 transition from PDT restrictions to intraday margin standards.','https://robinhood.com/us/en/support/articles/pattern-day-trading/'),
 ('Robinhood, Trading fees','Equity commissions and regulatory charges.','https://robinhood.com/us/en/support/articles/trading-fees-on-robinhood/'),
 ('Alpaca, About Market Data API','Basic versus Algo Trader Plus retail data plans and authentication.','https://docs.alpaca.markets/us/docs/about-market-data-api'),
 ('CME, Micro E-mini S&P 500 contract specifications','MES multiplier and minimum tick.','https://www.cmegroup.com/markets/equities/sp/micro-e-mini-sandp-500.contractSpecs.html'),
 ('Model Context Protocol, Build an MCP client','Deterministic programmatic tool calls are a protocol capability; broker access is a separate question.','https://modelcontextprotocol.io/docs/develop/build-client'),
 ('ProShares, TQQQ','Daily leveraged investment objective; actual fund prices used in the tests.','https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq'),
 ('ProShares, SQQQ','Daily inverse leveraged investment objective.','https://www.proshares.com/our-etfs/leveraged-and-inverse/sqqq'),
 ('Concretum, Backtesting Data Quality: Can Your Data Provider Be Trusted?','Provider comparison and sensitivity to stale bars, extrema and bar boundaries.','https://concretumgroup.com/backtesting-data-quality-can-your-data-provider-be-trusted/'),
 ('NYSE, Hours and calendars','Regular session hours and shortened sessions.','https://www.nyse.com/markets/hours-calendars'),
 ('Concretum, ORB Strategy Backtest in Python Using Alpaca','Historical SIP data access using a free account and paper API keys.','https://concretumgroup.com/orb-strategy-backtest-in-python-using-alpaca-10-years-of-free-data/')
]
(ROOT/'sources.json').write_text(json.dumps([{'id':i+1,'title':s[0],'scope':s[1],'url':s[2],'checked':'2026-09-08'} for i,s in enumerate(sources)],indent=2))

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#888888','axes.labelcolor':'#222222','text.color':'#222222','figure.facecolor':'white','axes.facecolor':'white'})
fig,ax=plt.subplots(figsize=(7.0,2.9))
x=np.array([r['cost_bps'] for r in rb['cost_results']]);y=np.array([r['event_weighted_mean_net_bps'] for r in rb['cost_results']])
lo=np.array([r['event_weighted_net_ci95_bps'][0] for r in rb['cost_results']]);hi=np.array([r['event_weighted_net_ci95_bps'][1] for r in rb['cost_results']])
ax.errorbar(x,y,yerr=[y-lo,hi-y],fmt='o-',color='#222222',capsize=5,lw=1.4)
ax.axhline(0,color='#999999',ls='--',lw=1);ax.set_xticks(x);ax.set_xlabel('Assumed round-trip cost (basis points)');ax.set_ylabel('Mean net event return (basis points)')
ax.grid(axis='y',alpha=.18);fig.tight_layout();fig.savefig(FIG/'rebound_costs.png',dpi=190);plt.close(fig)
close=pd.DataFrame(read('closing_daily'));curves=[]
fig,ax=plt.subplots(figsize=(7.0,2.0))
for base,col,ls in [('QQQ','#111111','-'),('SPY','#777777','--')]:
 q=close[(close.base==base)&(close.variant=='all')&(close.cost_bps==5)].copy()
 ax.plot(pd.to_datetime(q.date),q.equity,label=f'{base} direction, actual leveraged ETFs',color=col,ls=ls,lw=1.35)
ax.axhline(2500,color='#aaa',lw=.8);ax.set_ylabel('Simulated account value ($)');ax.legend(frameon=False,fontsize=8,loc='lower left');ax.grid(axis='y',alpha=.15);fig.autofmt_xdate();fig.tight_layout();fig.savefig(FIG/'closing_equity.png',dpi=190);plt.close(fig)
pr=pd.DataFrame(read('rebound_portfolio_daily'))
fig,ax=plt.subplots(figsize=(7.0,2.2))
for c,col,ls in [(0,'#999999',':'),(5,'#222222','-'),(10,'#666666','--')]:
 q=pr[pr.cost_bps==c]
 ax.plot(pd.to_datetime(q.date),q.equity,label=f'{c} bps round trip',color=col,ls=ls,lw=1.4)
ax.axhline(2500,color='#aaa',lw=.8);ax.set_ylabel('Simulated account value ($)');ax.legend(frameon=False,fontsize=8);ax.grid(axis='y',alpha=.15);fig.autofmt_xdate();fig.tight_layout();fig.savefig(FIG/'rebound_portfolio.png',dpi=190);plt.close(fig)

sty=getSampleStyleSheet()
sty.add(ParagraphStyle(name='MainTitle',fontName='Helvetica-Bold',fontSize=23,leading=27,spaceAfter=17))
sty.add(ParagraphStyle(name='PageTitle',fontName='Helvetica-Bold',fontSize=17,leading=21,spaceAfter=14))
sty.add(ParagraphStyle(name='Sub',fontName='Helvetica-Bold',fontSize=11.5,leading=15,spaceBefore=11,spaceAfter=6))
sty.add(ParagraphStyle(name='BodyResearch',fontName='Helvetica',fontSize=10.2,leading=14.4,spaceAfter=9))
sty.add(ParagraphStyle(name='SmallResearch',fontName='Helvetica',fontSize=8.5,leading=11.3,spaceAfter=6,textColor=colors.HexColor('#444444')))
sty.add(ParagraphStyle(name='CellResearch',fontName='Helvetica',fontSize=9.2,leading=12))
sty.add(ParagraphStyle(name='SourceResearch',fontName='Helvetica',fontSize=8.25,leading=10.5,spaceAfter=7))
story=[]
def p(t,style='BodyResearch'):story.append(Paragraph(t,sty[style]))
def title(t,first=False):p(t,'MainTitle' if first else 'PageTitle')
def sub(t):p(t,'Sub')
def table(headers,rows,widths):
 data=[[Paragraph('<b>'+escape(str(v))+'</b>',sty['CellResearch']) for v in headers]]
 data += [[Paragraph(str(v),sty['CellResearch']) for v in row] for row in rows]
 t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#777777')),('LINEBELOW',(0,1),(-1,-1),.35,colors.HexColor('#dddddd')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 story.extend([t,Spacer(1,9)])
def figure(name,w=510):
 im=ImageReader(str(FIG/name));iw,ih=im.getSize();story.append(Image(str(FIG/name),width=w,height=w*ih/iw));story.append(Spacer(1,6))
def page():story.append(PageBreak())
def cite(ids):
 p('Sources: '+ '; '.join(f'[{i}] <link href="{escape(sources[i-1][2], {chr(34):"&quot;"})}" color="#333333">{escape(sources[i-1][0])}</link>' for i in ids)+'.','SmallResearch')

title('Research before the trading bot',True)
p('<b>Decision: do not deploy capital yet.</b> The strongest remaining research lead is a sector-confirmed rebound in a temporarily lagging stock. It has a plausible economic mechanism and a small positive raw signal. Our initial finite-capital replay loses money after costs. Neither this idea nor the tested momentum alternatives currently has evidence strong enough to claim market-beating profitability.')
p('This research uses the stated $1,000-$5,000 starting budget, a $2,500 worked account, willingness to tolerate a 25% drawdown, and permission to consider another broker. Research was completed on September 8, 2026. Price history ends September 4; the incomplete September 8 session is excluded.')
table(['Test','Initial evidence','Decision'],[
 ['Sector-confirmed rebound','59 events: +0.102% average gross 30-minute return. After 0.10% cost: +0.002%.','Continue research only.'],
 ['Rebound with capital limits and stops','41 trades over 39 sessions: -0.14% account return at 5 bps cost; -0.54% at 10 bps.','Fails a live-build gate.'],
 ['Follow the day into the close','701 sessions: -24.96% for the QQQ implementation and -26.13% for SPY, at 5 bps cost.','Deprioritize these rules.'],
 ['Unusually active stock breakouts','39-session selected-stock test: -6.24% or -1.56% at 10 bps, depending on within-bar chronology.','No positive confirmation.']
],[141,248,121])
p('A basis point (bp) is 0.01%. Costs in this memo are <b>round-trip costs on traded notional</b>, including an assumed allowance for spread, slippage and fees. Account returns and per-event returns are different quantities and are labeled separately.')
sub('What was actually done')
p('Read original research and current broker documentation; downloaded and preserved raw vendor data; declared the initial experiments before viewing their results; tested costs and ambiguous fills; compared rebound outcomes with peer outcomes; and replayed the rebound with finite capital. The bundle includes the research scripts, parameters, raw responses, hashes and every tested variant. No trading bot, account integration or orders were created.')
p('The useful outcome is a falsifiable direction and several ideas we can stop spending money on. Increasing risk before the sign of net expectancy is established would amplify an unknown or negative edge. A daily trade opportunity is a reasonable design goal; positive profit every day is not a supported forecast.')
cite([1]);page()

title('The idea worth investigating further')
p('<b>Buy a stock that lags a confirmed rebound in its peers, only after the stock itself starts stabilizing.</b> The intended opportunity lasts tens of minutes, so it can be evaluated with simple arithmetic and ordinary software. It does not require an LLM, forecasting headlines or competing for microsecond execution.')
sub('Economic mechanism, and its competing explanation')
p('A stock price can be decomposed conceptually into a common market/sector component, persistent company information and temporary order pressure. Basket selling can push correlated stocks down together. Once peers recover, they provide a contemporaneous reference for the common component. A laggard may still contain temporary selling pressure that subsequently dissipates. This is our hypothesis, not an established fact about these events.')
p('The competing explanation is damaging: the laggard is correctly incorporating adverse company information. It can remain cheap relative to peers and keep falling. Broad peer confirmation and a positive recent bar reduce ambiguity but do not identify the cause. That is why a raw relative-price gap cannot be treated as free profit.')
sub('Exact initial screen')
p('At a completed five-minute bar, using at least three other stocks in the assigned peer group:')
table(['Step','Rule used in the event study'],[
 ['1. Shared decline','Over the preceding 15-minute decline window, the median peer return is at most -0.30%; at least 70% of peers are down; the target stock is also down.'],
 ['2. Peer recovery','During the subsequent 10 minutes, median peer recovery is at least half the magnitude of that peer decline.'],
 ['3. Stock lag and stabilization','Peer recovery exceeds stock recovery by at least 0.30 percentage points, and the stock\'s latest completed five-minute close exceeds its preceding close.'],
 ['4. Measured outcome','Enter at the following bar open; measure the stock\'s return to the open 30 minutes later. Screen roughly 10:05-14:30 ET; impose a 40-minute signal cooldown per stock.']
],[136,374])
p('The live signal would use only information completed before entry. Our screen uses simple returns and hand-assigned groups, not fitted beta or a news classifier. These are deliberately transparent pilot definitions. Group quality, signal age and company-specific news remain unresolved.')
sub('What would make the idea valuable')
p('The lag must predict subsequent return beyond ordinary sector exposure, the rebound must be large enough to pay actual execution costs, and competing signals must fit a small account. An improvement must survive an untouched test period. Merely choosing a stricter threshold after looking at the profitable events would not establish alpha.')
p('A future version could estimate the stock\'s normal sensitivity to peers using only past observations and normalize the residual by recent volatility. That is a proposed refinement, not part of the reported results. No refinement is being promoted as profitable.')
page()

title('The raw rebound signal is small and uncertain')
p('The five-minute stock sample contains 59 complete sessions, June 12-September 4, 2026. The first 20 sessions are reserved for warmup, leaving 39 screened sessions, July 14-September 4. Across 37 liquid, currently listed stocks in seven groups, the rules produced <b>59 events on 24 days</b>, in 19 different stocks. This current-universe selection is a limitation, especially for any future long-history test.')
figure('rebound_costs.png')
p('Figure 1. Mean stock return per event, after each assumed cost. Error bars are approximate 95% intervals from 20,000 circular five-session block resamples. All events on a day stay together; resampled total return is divided by resampled event count. These intervals are conditional on this small, selected dataset and are not adjusted for research across strategies.','SmallResearch')
table(['Round-trip cost','Mean net event return','Approx. 95% interval'],[
 [f'{r["cost_bps"]} bps',f'{r["event_weighted_mean_net_bps"]:.2f} bps',f'{r["event_weighted_net_ci95_bps"][0]:.2f} to {r["event_weighted_net_ci95_bps"][1]:.2f} bps'] for r in rb['cost_results']
],[142,173,195])
p('Peers gained an average 2.99 bps during the same 30-minute holding windows; the stock gained 10.24 bps. The unhedged, arithmetic excess was therefore <b>7.25 bps before costs</b>. Its approximate 95% block interval was -1.14 to +15.62 bps. This is a diagnostic comparison with the peer average, not a tradable hedged profit or a regression alpha estimate.')
p('The excess versus peers was similar in the two chronological halves, 7.14 and 7.44 bps, but only 38 and 21 events support those figures. Forty of the 59 events were semiconductor stocks. Up to seven events occurred on one day. These observations are not 59 independent bets.')
p('Even the gross interval includes zero. The evidence does not yet distinguish a useful edge from sampling noise. A cheaper fill would help the arithmetic, but passive orders cannot be assumed filled whenever prices merely touch a limit.')
cite([1]);page()

title('A signal is not yet an account-level strategy')
p('After inspecting the raw results, we ran a separate, explicitly exploratory portfolio replay. This addresses whether capital limits, overlapping signals and a protective stop erase the apparent opportunity. It is a new implementation check, not an untouched validation sample.')
table(['Replay rule','Implementation'],[
 ['Position and concentration','At most two positions and one per peer group. Simultaneous signals ranked by the observed residual gap, then ticker.'],
 ['Sizing','Whole shares; at most 25% of realized account equity per position; at most 0.25% planned equity loss including cost. No borrowing.'],
 ['Stop and exit','Initial stop is the lowest low of the five completed bars before entry, minus $0.01. Exit at the stop or the 30-minute time exit. A gap through the stop uses the worse bar open.']
],[135,375])
figure('rebound_portfolio.png')
p('Figure 2. Exploratory account replay, $2,500 starting capital. The plotted values are simulated realized end-of-day equity; intraday drawdown and execution failure can be worse.','SmallResearch')
table(['Round-trip cost','Trades','Ending account','Total return'],[
 [f'{r["cost_bps"]} bps',str(r['trades']),f'${r["ending_equity"]:,.2f}',f'{r["total_return"]:.2%}'] for r in portfolio
],[135,65,170,140])
p('All four cost settings admitted 41 trades on 22 days; 19 trades stopped out. Average entry notional was about $497. Gross profit was only $6.75. At 5 bps, approximately $10.19 of trading costs converted that to a $3.43 loss. At 10 bps, the loss was $13.62.')
p('This does not prove that every possible rebound strategy fails. It does show that the specific raw signal is too weak to support our first practical implementation. We should not remove the stop, add leverage or widen the universe solely to rescue this result. Those changes need their own predeclared tests. No annual return is inferred from these 39 sessions.')
cite([1]);page()

title('Following the day into the close failed this test')
p('There is a plausible mechanical basis for late-day continuation: investors that must restore fixed exposure can trade in the direction of the day\'s move. Baltussen and coauthors document intraday momentum across more than 60 futures markets and connect it to hedging demand. Their evidence covers a different universe and history; it is not proof that our present ETF implementation works.<super>[5]</super>')
p('For a fixed-leverage portfolio, a small-return approximation to the required rebalance is <b>L(L - 1)Ar</b>, where L is target leverage, A is starting equity and r is the underlying return. A +3x fund implies about 6Ar and a -3x fund about 12Ar in directional exposure adjustment. This derivation assumes no investor flows and ignores offsetting swaps, dealers and anticipation. It is a mechanism to test, not a calculation of net market buying.')
sub('Independent implementation')
p('At 15:30 ET, use the underlying ETF\'s return since the previous session\'s close. Buy the bullish leveraged ETF if positive, the inverse ETF if negative. Allocate at most 50% of account equity in whole shares. Exit at the close or a 1% adverse move in the purchased ETF. Use actual TQQQ/SQQQ or UPRO/SPXU prices. Full sessions only; prior-close and volatility history retain shortened sessions. Costs are charged on entry notional.')
figure('closing_equity.png')
table(['701 sessions; 5 bps cost','QQQ direction','SPY direction'],[
 ['Total account return','-24.96%','-26.13%'],
 ['End-of-day maximum drawdown','27.29%','26.21%'],
 ['Average gross trade return','-3.68 bps','-3.98 bps'],
 ['Only large daily moves: total return','-15.69%','-13.23%']
],[258,126,126])
p('The sample runs November 8, 2023-September 4, 2026 after warmup. Requiring both a large move and agreement with the intraday direction also lost money. Removing the stop did not rescue average gross returns. All 354 overlapping ETF session checks matched hourly and five-minute final-half-hour opens and closes exactly. This is an internal consistency check, not independent quote validation.')
p('We do not reverse the signal and call the resulting contrarian rule validated. That would be a new hypothesis chosen after seeing the data.')
cite([1,5,14,15]);page()

title('Opening breakouts: impressive papers, weak confirmation')
p('A 2024 study reports 41.6% compound annual growth for five-minute stock breakouts filtered by opening relative volume, versus 3.2% without that selection. It studies 2016-2023, permits long and short positions and up to 4x notional leverage, and includes per-share commissions. Its 15-, 30- and 60-minute versions report 17.4%, 2.3% and 4.1% respectively. These results motivate a test, but the sensitivity to the opening window is substantial.<super>[2]</super>')
p('QuantConnect published a separate implementation, but its displayed research run covers only 2016. A related QQQ/TQQQ paper explicitly assumes no slippage. These are useful primary references, not evidence that a $2,500 account can reproduce the headline returns.<super>[3,4]</super>')
sub('Our practical stock variant')
p('Choose up to three stocks whose first five-minute bar is positive and whose opening volume is at least 1.5 times its prior 14-session opening average. Require price above $5, prior 14-session average volume of at least one million shares and ATR above $0.50. Buy a break above the opening high by $0.01 before 11:00; stop at 0.1 ATR below entry; exit by 15:55. Cap each position at one-third of equity and 0.25% planned risk including cost.')
table(['At 10 bps; 39 sessions','Conservative chronology','Favorable chronology'],[
 ['Selected high-volume top-three variant','-6.24% account return','-1.56% account return'],
 ['Lower volume cutoff of 1.0','-8.46%','-3.03%'],
 ['All eligible positive-opening stocks','-1.49%','+0.59%']
],[236,137,137])
p('A five-minute candle can contain both a breakout and the stop price without telling us which occurred first. The conservative simulation stops an ambiguous trade; the favorable simulation allows its low to precede entry unless its close proves a later stop crossing. In the core variant, 45 of 58 cost-adjusted executed trades were ambiguous. The favorable run executed 59 trades because compounding and share rounding changed capacity.')
p('These are two within-bar chronology assumptions, not statistically estimated performance bounds. The core strategy is negative under both. The small positive favorable result in the broad baseline cannot establish a tradable edge. Our 37-stock, long-only universe and short period also differ materially from the paper\'s broad long/short experiment.')
sub('Another disclosed follow-up')
p('We also tested the QQQ first-five-minute direction, purchasing TQQQ or SQQQ at 09:35, with the purchased ETF\'s opening low as its stop and a 15:55 exit. This additional exploratory test lost 3.94% over 39 trades at 10 bps. A relative-volume filter admitted only two trades and lost 0.67%. Neither result justifies building it.')
p('The original authors\' later data-quality investigation found materially different results across providers and identified stale bars, price extrema and bar-boundary assignment as causes. Our own ambiguity check makes those concerns directly relevant.<super>[16]</super>')
cite([2,3,4,16]);page()

title('Broker choice must follow the economics')
table(['Market or expense','Small-account implication'],[
 ['Liquid stocks and ETFs','The most plausible starting instruments: granular share sizing, observable prices and potentially low execution costs. The tested edge must still clear spread and slippage.'],
 ['Robinhood crypto','The published entry taker tier is 0.95% per side; exact buy/sell fee break-even is about 1.918%, before any additional price disadvantage. This rules out a tiny-move scalp at that tier. API maker/taker rollout can affect actual charges. [6,7]'],
 ['Micro S&P futures','MES is $5 per index point, with a 0.25-point tick. A 20-point stop risks $100 before costs: 4% of a $2,500 account. Small margin requirements do not make the underlying price risk small. [12]'],
 ['Short-dated options','Premium collection can conceal infrequent large losses. Without a separately tested volatility-pricing edge, it is not a solution to the daily-consistency objective. No option strategy was backtested here.'],
 ['$99 monthly data plan','$1,188 per year consumes 47.52% of $2,500 starting capital, before trading losses or taxes. At $1,000 it is 118.8%; at $5,000, 23.76%. Avoid that fixed expense during initial research. [11]']
],[133,377])
sub('Robinhood is more capable than the old crypto-only assumption')
p('Current Robinhood documentation lists long equities, options and crypto through its Agentic trading tools, including equity quotes, orders and cancellation. Limited margin allows reuse of unsettled proceeds, but does not allow borrowing; a cash account waits one business day for equity/option sale proceeds. Robinhood also says the $25,000 PDT requirement was removed from its margin accounts effective June 4, 2026, with new intraday margin standards. Account eligibility still needs verification.<super>[8,9]</super>')
p('These strategies need no AI at trade time. MCP supports programmatic tool calls, but we have not verified Robinhood authentication, permitted unattended custom-client use, rate limits, quote coverage or broker-held stop support for the intended local program. Those are specific integration gates. A protocol capability is not proof of working brokerage access.<super>[8,13]</super>')
sub('Least-expensive next research path')
p('Alpaca\'s free Basic plan provides historical data since 2016 with a restriction on the latest 15 minutes; stock endpoints require authentication. Its free real-time feed is IEX, while the $99 plan covers all US exchanges. A SIP-volume strategy cannot silently substitute IEX volume at deployment. Published instructions demonstrate historical SIP access with paper API keys, so a free data account is the next practical source to verify locally.<super>[11,18]</super>')
p('No account needs funding for that historical research. Credentials should stay in a local secret store. If Robinhood cannot support the required deterministic client and data at acceptable cost, use a documented broker API such as Alpaca after checking that account\'s actual trading constraints. Brokerage choice does not repair a negative strategy.')
cite([6,7,8,9,10,11,12,13,18]);page()

title('The math of aggression and consistency')
p('Let R be the planned loss before costs, p the win probability, b the average winning payoff in R, and k the round-trip cost in R. Under a simplified fixed-win/fixed-loss model:')
p('<b>Expected net R per trade = p b - (1 - p) - k.</b><br/><b>Break-even win probability = (1 + k) / (1 + b).</b><br/><b>k = round-trip cost in bps / stop distance in bps.</b>')
p('Illustration only: 40% winners averaging 2R and 60% losers at -1R produce +0.20R gross expectancy. If a 50 bp stop incurs 10 bp of cost, k = 0.20 and the entire arithmetic edge disappears. With 5 bp cost, k = 0.10 and the assumed net edge is +0.10R. None of those win/payoff assumptions was established by our tests.')
sub('Risk can magnify edge; it cannot create it')
p('If each trade risks fraction f of equity, expected log growth in this simplified model is p ln[1 + f(b - k)] + (1 - p) ln[1 - f(1 + k)]. At zero arithmetic expectancy, volatility still makes geometric growth negative. Leverage against an unproven edge can therefore accelerate drawdown without improving its foundation.')
table(['Loss per stopped trade','Losses in a row to exceed 25% drawdown'],[
 ['0.25% of then-current equity','115'],['0.50%','58'],['1.00%','29'],['2.00%','15'],['4.00%','8']
],[215,295])
p('This is only the algebra of a consecutive loss streak, not a ruin-probability estimate. Mixed wins and losses, correlated sector trades, gaps and failed exits can also produce a 25% drawdown. A stop defines intended risk, not a guaranteed loss limit.')
sub('A positive edge can still produce many losing days')
p('In the hypothetical 40%-win, 2R-payoff model with 0.10R cost and exactly three independent trades per day, at least two winners are needed for a profitable day. That occurs only 35.2% of the time even though expected profit is positive. Correlation makes daily outcomes less diversified. Maximizing green days is a different objective from maximizing sustainable net growth.')
sub('Small edges require substantial evidence')
p(f'The rebound event-return standard deviation was {rb["gross_sd_bps"]:.1f} bps. If observations were independent, detecting a true 5 bp net mean with a two-sided 5% test and approximately 80% power would require about {diag["math"]["n_for_80pc_power_at_5bps_net"]:,.0f} events: ((1.96 + 0.842) x 64.8 / 5)<super>2</super>. Clustering and strategy selection make that optimistic. Fifty-nine events cannot bear the weight of a large return forecast.')
p('For scale, $25 per day on $2,500 is 1% daily. Compounded for 252 sessions, that would exceed 1,100% annually. It should not be a baseline target. The editable workbook exposes these assumptions so capital, cost and risk can be changed without confusing a scenario with measured alpha.')
page()

title('A concrete research gate before building')
p('<b>Continue with one candidate: the sector-confirmed rebound.</b> Treat it as a hypothesis to falsify, with the present conclusion recorded as “no demonstrated net edge.” Do not build an execution engine around the current results. The immediate deliverable should be a longer historical test and quote-based execution study.')
table(['Stage','Evidence required before advancing'],[
 ['1. Data audit','Obtain several years of minute bars and, where available, bid/ask history using locally configured data-only access. Verify split handling, calendar sessions, missing bars and historical symbol coverage. Use a point-in-time liquid-stock universe or explicitly report the surviving-universe limitation.'],
 ['2. Freeze the experiment','Keep the existing raw rule as the baseline. Permit at most two declared refinements, such as lagged beta/volatility normalization and a mechanical company-event exclusion. Fix costs, exits, group construction and position limits before reading the reserved results.'],
 ['3. Chronological validation','Use earlier years for development and reserve an unseen stock-minute period such as 2024-2025 for one final evaluation. The already viewed 2026 pilot is not a holdout. Test falling, rising and high-volatility periods; purge overlapping holding windows at split boundaries.'],
 ['4. Economic and risk gate','Require positive net expectancy at realistic 10 bp cost and positive performance under a 20 bp stress, with a block-based lower confidence bound above zero after accounting for the small declared family of variants. Compare net return with cash and SPY, report beta, turnover and capital usage, and assess drawdown versus 25% tolerance. These are proposed gates, not passed results.'],
 ['5. Forward observation','Collect at least 30-60 sessions of live quotes and shadow orders after rules are frozen. Measure attainable fills, latency, missed fills and stop slippage. A simulated touch at a limit price is not proof of a fill. Only then decide whether a tiny funded execution trial is justified.']
],[120,390])
sub('What would kill the idea')
p('Abandon it if the apparent gain is explained by peers, vanishes at attainable costs, depends on one sector or a handful of days, or disappears in reserved data. If two bounded refinements fail, move to a different economic hypothesis instead of searching hundreds of thresholds. An unprofitable strategy is not rescued by a larger account or more frequent trades.')
sub('Scaling policy, only after the evidence changes')
p('A later trial could begin at 0.25% planned risk per trade, one position per sector, with a daily loss stop and a drawdown-based suspension. Increasing toward 0.5% risk would require observed execution and net performance consistent with the research. A 25% tolerance is a ceiling for evaluating tail risk, not an instruction to run the account down to that level. Exact live controls still require broker capability checks and a separate test.')
p('The unresolved bottleneck is authenticated long-history data and execution evidence. There is no reason to pay for AI inference, premium live data or a trading bot before this gate is passed. The research archive is reproducible analysis only.')
page()

title('Sources and reproducibility')
p('All web sources were checked September 8, 2026. Bracketed numbers in the memo map to the primary references below. Quantitative results without an external attribution are our calculations from the saved vendor responses. Published performance was not adopted as our own.','SmallResearch')
for i,(name,scope,url) in enumerate(sources,1):
 p(f'<b>[{i}] <link href="{escape(url, {chr(34):"&quot;"})}" color="#333333">{escape(name)}</link>.</b> {escape(scope)}','SourceResearch')
sub('Audit notes')
p('The initial experiment plan was written before inspecting results; follow-up plans label later diagnostics. Invalid OHLC rows and incomplete trading sessions were excluded from execution tests. A request labeled daily returned monthly granularity and was excluded entirely. Prior-close history was corrected to retain shortened sessions. Intraday fills, costs and stops remain simulations; no NBBO, latency, dividends on intraday holdings, taxes, cash interest or infrastructure expense was separately modeled. Regulatory charges are represented only by the aggregate cost assumption. The archive preserves raw inputs and output tables; the workbook holds the chart data, event records and editable arithmetic.','SmallResearch')

def footer(canvas,doc):
 canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#777777'));canvas.drawRightString(561,27,str(doc.page))
doc=SimpleDocTemplate(str(OUT/'Trading_Strategy_Research.pdf'),pagesize=(612,792),rightMargin=51,leftMargin=51,topMargin=43,bottomMargin=43,title='Research before the trading bot',author='')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(str(OUT/'Trading_Strategy_Research.pdf'))
