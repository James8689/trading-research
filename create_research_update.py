"""Create the readable research decision record from saved results."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent
d=json.loads((R/'daily_results/results.json').read_text())
v=json.loads((R/'volume_results/results.json').read_text())
names={'overnight_always':'Overnight, every session','overnight_trend':'Overnight, trend filter','trend_fixed50':'Trend, 50% entry allocation','trend_vol18':'Trend, volatility sizing','buy_hold':'Buy and hold'}
def table(period):
 lines=['| Method | Instrument | Annualized return | Worst closing drawdown | Ending $2,500 | Orders |',
        '|---|---|---:|---:|---:|---:|']
 for x in d:
  if x['split']!=period or x['roundtrip_cost_bps']!=10:continue
  lines.append(f"| {names[x['method']]} | {x['etf']} | {100*x['cagr']:.2f}% | {abs(100*x['eod_max_drawdown']):.2f}% | ${x['ending_equity']:,.2f} | {x['orders']:,} |")
 for x in v:
  if x['split']!=period or x['roundtrip_cost_bps']!=10:continue
  name=f"Volume shock, {x['horizon']} sessions" if x['method']=='volume_shock' else 'Monthly equal weight, same surviving stocks'
  lines.append(f"| {name} | Stocks | {100*x['cagr']:.2f}% | {abs(100*x['eod_max_drawdown']):.2f}% | ${x['ending_equity']:,.2f} | {x['orders']:,} |")
 return '\n'.join(lines)
text='''# Automated trading research: completed second research batch

September 8, 2026. Offline historical simulations; no trading orders submitted.

**Decision: none of the tested strategies meets the combined objective of frequent opportunities, strong returns and a credible 25% drawdown budget. Do not build or fund these rules on the strength of these results.** Several made money historically. That is a weaker result than demonstrating an exploitable edge or dependable daily income.

The starting account is $2,500, within the $1,000–$5,000 research budget. All strategies are deterministic and require no AI inference when trading. The research deliberately preserved failed variants and transaction-cost sensitivity instead of changing thresholds until something looked attractive.

## What this batch established

Daily histories were downloaded for SPY, QQQ, SSO, QLD and the same 37 stocks used in the earlier intraday study. Thirty-eight histories have 4,194 daily rows each from January 4, 2010 through September 4, 2026. META has 3,595 rows from its May 18, 2012 IPO. There are 41 histories total: 40 have 4,194 rows, and META has 3,595. The preceding sentence's aggregate count is clarified by this exact total. All study returns below use 2011–2025; 2010 warms up indicators. Explicit daily timestamps were checked because an earlier maximum-range vendor request silently returned monthly data.

The rules were frozen before viewing these new strategy results. Parameters stayed unchanged between 2011–2021 diagnostics and the reserved 2022–2025 evaluation. Both periods start with a fresh $2,500 account. The full 2011–2025 simulation is a separate continuous run. This is retrospective evaluation, not a genuinely untouched future test: the research has examined several hypotheses and uses a present-day stock universe.

Costs below are 10 basis points, or 0.10% of traded notional per round trip, modeled as 0.05% on each actual side. This is an assumed allowance for execution friction, not a measured Robinhood or Alpaca fee. Data subscriptions, computer costs, taxes and interest on idle cash are excluded. Whole shares and available cash constrain strategies; passive index benchmarks use fractional, fully reinvested total returns so cash drag does not artificially weaken them.

## Reserved evaluation: January 2022–December 2025

'''+table('reserved')+'''

Orders count buys and sells separately. A completed two-sided trade normally contributes two orders. The equal-weight benchmark's order count represents modeled monthly constituent adjustments, not a whole-share executable account.

## Full-history check: January 2011–December 2025

'''+table('all')+'''

The QLD trend rule is the most useful simple reference strategy in this batch, but it does not satisfy the brief. Its roughly 11.9% annualized reserved return came with few trades, and its longer-history drawdown reached roughly 32%, beyond the 25% research budget. Buying QQQ outright returned more over the full period. Choosing only the recent favorable drawdown would misrepresent the evidence.

## The concrete new idea and why it was rejected

The economic hypothesis was gradual absorption of company-specific information. A sharp stock rise on unusually heavy volume, much stronger than the broad market and closing near its high, could reflect sustained demand that continues after the first day. This is an inference, not a verified explanation of any specific trade. No earnings timestamp, analyst revision or news confirmation was available in this signal.

At each completed close, require all of the following:

1. Stock total return minus SPY return is at least the larger of 3% or 1.5 times its trailing residual volatility. Volatility uses the preceding 20 completed sessions.
2. Volume is at least twice its preceding 20-session mean.
3. The close is in the top quarter of the daily range; nominal share price is at least $5; preceding average daily dollar volume is at least $20 million.
4. No split has occurred in the preceding 20 sessions, including the event day.

Enter at the next session's modeled open if it remains above the event-day low minus one cent. Simultaneous events rank by market-relative return divided by prior volatility, then ticker. Hold at most four positions, one per stock and original peer group. Allocate no more than 25% of equity to one position and no more than 0.5% of equity to its intended stop-loss risk, including modeled costs. Use whole shares and no borrowing.

Exit at the event low minus one cent, or at the open after five or 20 full sessions. A gap below the stop exits at the worse opening price. Both holding periods were declared before testing; no profit target creates same-bar ordering ambiguity. These are price-bar simulations, not proof that an order can observe and fill the auction open at exactly that price.

The 20-session portfolio completed 81 reserved-period trades. It earned $245.75 after modeled costs, with 5.13% worst closing drawdown and only 8.32% average end-of-day stock exposure. Five trades earned $264.31 combined, more than the entire portfolio profit. Removing those P&Ls while keeping the original trades and sizes would leave a loss; this is a concentration diagnostic, not a fresh counterfactual simulation. The five-session version was essentially flat.

A separate post-result diagnostic examines all 154 qualifying reserved-period events with a complete 20-session window, without portfolio constraints or stops. Their average return after 10 basis points was +1.87%, but the approximate 20-session-block 95% interval ran from -0.20% to +4.08%. Gross relative performance against same-group peers averaged -0.39%, with an interval of -1.79% to +1.05%. Relative performance against QQQ averaged +0.57%, with an interval of -1.18% to +2.59%. These intervals do not correct for the broader search across hypotheses. They do not establish positive stock-selection alpha. Both 20- and 60-session block results are saved.

Increasing leverage would amplify the same uncertain signal. Broadening to smaller stocks might increase event frequency, but it would also change the universe, execution costs and evidence. Neither change is justified as a proven improvement by this test.

## Exact index rule definitions

Overnight versions buy SSO or QLD at the prior close with a 50% account allocation and sell at the following open. The trend-filtered version requires the corresponding base ETF, SPY or QQQ, to be above its 200-session average on the completed day before entry day. This deliberate extra lag avoids relying on an entry-close signal that is known only after that close.

The lower-turnover trend versions check the base ETF's previous completed close against its 200-session average. They enter or exit the corresponding 2x ETF at the next modeled open. The fixed version targets 50% of account equity only when entering; its weight subsequently drifts. The volatility version targets the smaller of 100% ETF notional or 18% divided by its lagged 60-session annualized volatility, recalculated at month starts and trend-state changes. Neither borrows account cash. Actual ETF prices include the fund's embedded expenses and daily leverage behavior. QLD targets twice the Nasdaq-100's daily return; multi-day returns are not guaranteed to equal twice the index's return. [ProShares QLD](https://www.proshares.com/our-etfs/leveraged-and-inverse/qld)

Overnight compensation has a plausible inventory-risk foundation, but that does not validate this close-to-open ETF strategy. The New York Fed paper studies a particular overnight return pattern and its relationship to preceding order imbalances. Our rule is not a replication of that paper. [New York Fed, The Overnight Drift](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)

The complete files retain 0/2/5/10-basis-point index variants and 5/10/20-basis-point stock variants. For example, reserved QLD trend-filtered overnight returns fell from roughly 5.58% annualized at five basis points to 1.05% at ten. The low-turnover QLD reference changed only slightly, from roughly 11.89% to 11.87%. Frequent execution makes a small assumed cost error economically important.

## Data, account and execution limits

The source is Yahoo's daily chart endpoint, preserved as raw JSON with request URLs and SHA-256 hashes. Example: [QQQ historical chart request](https://query1.finance.yahoo.com/v8/finance/chart/QQQ?period1=1262304000&period2=1788825600&interval=1d&includePrePost=false&events=div%2Csplits). The snapshot is not a point-in-time institutional dataset. Vendor adjustments and revisions remain a risk.

Historical nominal OHLC prices are reconstructed from split-adjusted prices and reported corporate actions for whole-share sizing. Dividend cash is credited on the ex-date as an approximation to a receivable, rather than waiting for the actual payment date. Reconstructed total returns are compared with vendor adjusted-close returns; differences are recorded. Stock spin-offs represented as vendor adjustment ratios are an additional historical-universe caveat. No volume-strategy position actually crossed a recorded split in these runs. The original index benchmark was corrected to fully reinvested fractional total returns before conclusions were written.

The stock universe contains companies chosen today that survived. It omits failed and acquired historical alternatives and has sector concentrations. The same-universe benchmark exposes, but does not remove, that bias. META becomes eligible only after it has enough history. No missing held-position bar was silently filled. Summed realized trade P&L reconciles to the ending stock-strategy account balance.

Drawdown is measured from daily closing equity. It can understate intraday losses. Stops are planned risk limits, not guarantees against gaps. The simulator does not enforce account-specific trading permissions or settlement restrictions and allows sale proceeds to be reused. Current Robinhood documentation distinguishes cash accounts requiring one business day for stock sale settlement from limited-margin accounts that can reuse unsettled proceeds. These details must be implemented before an executable account replay. [Trading with your agent](https://robinhood.com/us/en/support/articles/trading-with-your-agent/)

Alpaca is connected. Small historical calls initially succeeded, including SIP quotes and January 2020 semiconductor bars. Subsequent calls, including a fresh six-bar request, failed with internal app errors. No entitlement conclusion or credential problem has been inferred. Existing successful data is preserved; bulk retries are paused.

Robinhood now documents an official Trading MCP and dedicated Agentic accounts, including long equities, options and crypto. Any earlier blanket statement that official automation is limited to crypto should be treated as outdated. Availability of that connector does not itself establish support for the intended standalone deterministic execution client; that integration remains untested. No new account, connection or trade was created. [Robinhood Agentic Trading overview](https://robinhood.com/us/en/support/articles/agentic-trading-overview/)

Alpaca paper results would still need an external execution audit: its documentation identifies omitted latency slippage, queue effects and other differences, and its simulator does not process dividends. Paper profitability alone would not settle the question. [Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading)

## What would justify the next build

The next research target should be an observable information event with a plausible persistent buyer, such as a timestamped earnings surprise accompanied by a guidance increase. That is a proposed hypothesis, not a finding. It needs historical release timestamps, figures available at the time, a historical stock universe including delistings, and executable price data. Current analyst estimates or a current earnings calendar cannot substitute for historical point-in-time surprises.

Keep the daily volume screen as a rejected baseline. Before another test, specify one event definition and one holding rule, reserve a new evaluation sample, and measure both net portfolio returns and incremental performance against comparable stocks. Require results that survive costs, multiple market conditions and concentration checks. If that evidence is positive, a local deterministic scanner and execution simulator become justified. No paid dataset or account change has been initiated.

## Resume without repeating the work

Start with `HANDOFF.md`, then `daily_experiment_plan.json` and `volume_shock_plan.json`. Completed results are in `daily_results/` and `volume_results/`; source histories and hashes are in `daily_raw/`. The daily and stock simulators, attribution diagnostic and download scripts are included. `checkpoint.py --save` preserves a versioned archive; do not blindly rerun downloads or change failed rules and label the new result an untouched test. The original intraday archive remains a separate saved artifact. Its referenced spreadsheet workbook was never completed; this update makes no claim that one exists.
'''
# Keep the exact coverage statement without a redundant earlier draft count.
text=text.replace('Thirty-eight histories have 4,194 daily rows each from January 4, 2010 through September 4, 2026. META has 3,595 rows from its May 18, 2012 IPO. There are 41 histories total: 40 have 4,194 rows, and META has 3,595. The preceding sentence\'s aggregate count is clarified by this exact total.',
 'There are 41 histories: 40 have 4,194 daily rows from January 4, 2010 through September 4, 2026; META has 3,595 rows from its May 18, 2012 IPO.')
(R/'deliverables/Trading_Research_Update.md').write_text(text)
print('Created Trading_Research_Update.md',len(text.split()),'words')
