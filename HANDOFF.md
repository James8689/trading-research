# Trading research handoff

## September 9: design expansion checkpoint 1

Latest user instruction is design/scaffold only; do not build out or activate the runner. Added design/README.md, NETWORK.md and STATUS.md. Corrected START_HERE and AGENT_NETWORK to distinguish intended behavior from the untested draft. AGENTS now points to the active design scope and incremental GitHub saves. Next: context/recovery, lifecycle, budget policy and acceptance/templates. Spending preference still unanswered. Frozen research plans and raw data unchanged.

## September 9, 2026: imported repo, batch 3, agent network

The full user-provided ZIP was extracted on Windows. Original git history and all cached data are preserved. Start with START_HERE.md and README.md for current status; older Linux Library upload instructions below are historical. checkpoint.py now supports a clearly labeled local-only save when that helper is absent.

Batch 3 has four independent agent reports, adversarial plan review and two hashed feasibility-only plans: B3-H1-v1 CEF reinvestment routing and B3-M2A-v1 capped cash-election allocations. Read research_batch3/SYNTHESIS.md. No new return test, large download, simulator or order was run. Other hypotheses and failures remain recorded.

James requested a private GitHub repo and an interchangeable frontier director/cheap-worker network with durable individual context. Configuration, role prompts, context/budget design, reproducibility docs and calibration fixtures are present. research_loop/runner.py was written by a worker that hit a usage limit before finishing tests. Treat it as an unverified draft, not operational unattended automation. Automatic calls are disabled and spending preference remains unresolved. Review and test runner before use; no background loop was launched.

The private GitHub publication is the immediate priority. Preserve original commits; include cached data, source reports and figures. Future coding agents should finish runner verification, then perform frozen document probes. Research gates and no-live-trading constraints remain in force.

## Direction for the next research agent: create, do not copy

James wants the next pass to use this archive as a starting point, not as a menu of published strategies to retest. His working theory is that widely published rules are competed away or too well known to provide much edge by themselves. Generate genuinely original hypotheses from first principles, using broad pretrained financial knowledge and careful reasoning to identify mechanisms that could still be underexploited. This is an instruction to be creatively ambitious, not permission to invent unsupported performance claims.

The next agent should first reason about *why* a trade might pay: who is forced to buy or sell, what information arrives with delay, what constraint prevents larger participants from harvesting the opportunity, and why the effect could survive realistic costs. Consider unusual combinations of market structure, accounting fundamentals, flows, corporate actions, tax/settlement constraints, cross-asset relationships, or operational behavior. AI should be used for hypothesis generation, feature construction, and falsification only when it adds real value; the eventual live rule should be deterministic and inexpensive unless evidence proves an always-on AI decision loop adds alpha after its cost and failure risk.

Do not simply take a known moving-average, RSI, breakout, overnight, volume, or momentum rule and add thresholds. Do not use the favorable historical result as the objective. Every new idea still requires a predeclared mechanism, a data-availability audit, realistic spread/slippage/latency assumptions, a no-lookahead implementation, a development period, an untouched validation period, and concentration/stability analysis. Preserve failed tests. Do not build or place trades until a candidate survives those gates and a small live quote/shadow-order test confirms that the modeled fills are attainable.

The current tested strategies are rejected or benchmarks, not the answer. The next promising research direction is a new hypothesis, not an endorsement of earnings-surprise trading: investigate whether a timestamped information/event mechanism creates delayed forced flows that can be measured point-in-time. The agent may reject this direction and propose a better one if its mechanism is stronger. Keep the $2,500 modeled starting account, approximately 25% drawdown ceiling, low-cost execution requirement, and durable checkpoint discipline unless James explicitly changes them.

## User objective and authorization
James wants an automated, low-cost trading strategy with frequent opportunities and a credible chance of beating passive returns. Research comes before building. Starting capital $1,000-$5,000, modeled at $2,500; tolerable drawdown 25%; Robinhood preferred but other brokers permitted. No trading orders, funding, paid subscriptions, or account changes authorized. Research scripts and read-only historical data access are authorized. No AI inference needed at trading time.

User explicitly requested conservative usage, durable batch checkpoints and sufficient notes for another bot to resume without repeating work.

## Persisted original work
- Original 10-page report: `deliverables/Trading_Strategy_Research.pdf`, Library ID `libfile_b08c9657fc5c81919691fd607d6218d9`.
- Original full archive: `Trading_Research_Archive.zip`, Library ID `libfile_5b0f5ae5abd08191aef9bb84985a4647`.
- Saved original archive contains 55 vendor responses, research scripts, plans, sources and 23 result files. The report references an editable workbook, but that workbook was NOT completed. Do not claim it exists.
- Original report was rendered to 10 page PNGs. Full visual inspection was not completed before an interruption. Do not claim full visual QA.

## Actual initial findings
- Sector rebound: 59 events on 24 of 39 screened sessions, July 14-September 4, 2026. Gross mean 10.237 bps, peer-relative gross mean 7.249 bps. Approximate event-weighted five-session block 95% interval for gross mean -1.942 to +21.675 bps. Forty events in semiconductors. No demonstrated positive net edge.
- Fixed-capital follow-up: 41 trades, 19 stops, 22 active days. $2,500 account, 25% notional cap per position, 0.25% planned risk, at most two positions and one per group. Account return +0.270% without costs, -0.1374% at 5 bps round trip, -0.5448% at 10 bps, -1.3596% at 20 bps.
- Closing momentum, November 8, 2023-September 4, 2026: 701 sessions. Actual long leveraged ETFs following QQQ/SPY direction into final 30 minutes. At 5 bps, total return -24.961% and -26.128%; stops did not explain away negative signal. Other variants lost too.
- Stock opening breakout selected top-three high-relative-volume names: 39 sessions, -6.239% conservative chronology and -1.556% favorable chronology at 10 bps. Most entries have same-five-minute-bar stop ambiguity. Broad baseline favorable chronology +0.59% is not validated performance. Follow-up index opening strategy -3.942% over 39 trades.
- All results are simulations on vendor OHLCV, not executable quotes. Current-stock universe creates selection bias. No strategy is validated. Do not promise profitability or annualize 39-session results.

## New Alpaca connection and verified access
The user connected Alpaca. Ignore older blockers saying not connected. Available tools are data-only `mcp__codex_apps__alpaca_*` functions in ALL_TOOLS.
- Successfully fetched SIP AAPL one-minute bars January 2, 2020 09:30-10:00 ET.
- Successfully fetched historical SIP AAPL bid/ask quotes January 2, 2020 09:35:00-09:35:01 ET.
- Successfully fetched all six semiconductor stocks' January 2020 five-minute bars in one call: 17,643 total including extended hours. Structured content has `bars`, `counts`, `request`, `tool`; values also duplicated in content text. Use structured content and print only counts.
- `get_stock_bars`: symbol string or list; start/end ISO; timeframe `5Min`; feed `sip`; limit; timezone `UTC`. No page token exposed. Large requests may be slow. Prefer bounded batches. Quotes accept analogous start/end and limit.
- No credential extraction is needed or permitted. Use the connected app, not copied secrets.

## Frozen extended experiment
Read `alpaca_extension_plan.json` before resuming. Same 37 stocks and seven groups from `groups.json`, same baseline signal and portfolio rules. Period 2020-2025; 2020-2023 diagnostics, 2024-2025 reserved evaluation. Do not tune between periods. Current-universe limitation must stay explicit. Five-minute bars suffice for the unchanged baseline; historical quotes can probe costs. Official calendar excludes half days for full-session tests.

## Current checkpoint status
Initial historical access confirmed. Extended return calculations have NOT been run. The request for all 37 stocks in January 2020 FAILED with a serialization error; do not count it as downloaded. The original six-symbol January 2020 probe was saved successfully as `alpaca_batches/2020-01_semiconductors.json` (17,643 bars including extended hours), and the 2020 official calendar as `alpaca_batches/calendar_2020.json`. Manifest records counts and SHA-256 hashes.

The extension checkpoint is saved under Library ID `libfile_f200104d709081918ad40d542aa390da`, local `deliverables/Trading_Research_Checkpoint.zip`. `checkpoint_receipt.json` retains its version for updates. The archive deliberately omits the original Yahoo raw files and source PDFs, which remain in the original persisted archive above.

Subsequent January 2020 requests for software, finance and energy returned `Mcp error: -32603: Internal error` immediately, including a sequential repeat for four software stocks. This is an app error, not demonstrated lack of subscription entitlement. Do not repeatedly retry bulk calls while this persists. A small MSFT six-bar request ALSO FAILED with the same internal error. Downloads are paused; no further retry was attempted. `EXTENSION_STATUS.json` records failed batch names. `download_alpaca_via_tools.js` implements resumable month/group batches, three concurrent reads, disk save before progression, monthly manifest updates and annual durable checkpoint. Error handling inspects `r.isError` before JSON.parse. Start with a tiny successful probe before invoking its download loop.

## Resume procedure
1. Inspect `alpaca_batches/manifest.json` if it exists. Treat only completed files with recorded counts/hashes as done. Never restart completed downloads blindly.
2. Read this handoff and `alpaca_extension_plan.json`; inspect existing code rather than rewrite core rules.
3. Download remaining history in bounded batches with 2-3 concurrent read calls. Save each completed batch before proceeding. Keep counts, first/last timestamp, request, provider, interval, feed and hash. Large tool responses should not be printed in chat.
4. Validate complete 78-bar regular sessions against calendar. Actual Alpaca intraday prices are unadjusted; within-day returns avoid split discontinuities. Do not use cross-day raw prices for returns without split handling.
5. Reuse/refactor vectorized event logic in `followup.py:rebound_fast` and fixed-capital logic in `portfolio_replay.py`. Do not run `analyze.py` main unnecessarily; its original pandas rebound loop is slow. Preserve original results in `analysis/`; put extended results in a new directory.
6. Save outcomes and methodology limitations, then update the handoff and durable archive. Do not select an attractive historical variant and call it validated.

## Durable saving
Library skill workflow was read earlier. Helper is `/root/.codex/plugins/cache/openai-curated-remote/openai-library/0.1.54/skills/library/scripts/library_upload.py`. Use a closed-stdin JSON batch with `uploads`, each absolute `local_path`, `purpose: create_library_file` for a new checkpoint; for existing identities use replacement with retained version guard. Helper owns preparation, transfer, finalize and local metadata. Inspect every result before claiming saved. Single small new file can alternatively use `library_create_library_file`, then apply returned xattrs.

Do not overwrite an existing Library file with a new create operation. Original user-facing report and archive identities above must be preserved on updates. New extension checkpoint can be a separate artifact.


## Daily-history alternative research, current turn
Alpaca six-bar probe still returns internal error. Continued useful work with public daily data rather than more app retries. `daily_experiment_plan.json` freezes two hypotheses before new results: overnight risk premium and lower-turnover trend/volatility exposure, SPY->SSO and QQQ->QLD. Four daily histories downloaded successfully, 4,194 rows each (2010-2026); explicit timestamp queries avoid the previous Yahoo max-range monthly-data problem. `daily_raw/manifest.json` preserves URLs and hashes. `test_daily.py` tests 2011-2025, 2011-2021 diagnostics and reserved 2022-2025 with costs 0/2/5/10 bps. The benchmark uses fractional fully reinvested total returns, while strategy uses whole shares, so benchmark is not weakened by cash drag. Results COMPLETED, including corrected benchmarks. All new files are included by checkpoint.py. No trades or new brokerage actions.

## Completed second batch, September 8, 2026

Read `deliverables/Trading_Research_Update.md` for complete, cited results and all index/stock variants at 10 bps. `create_research_update.py` regenerates it from saved result JSON. The checkpoint now includes Markdown deliverables. Original PDF is historical and is not updated; prefer this update for current findings.

### Daily index results
- `daily_results/results.json` contains 120 evaluations including costs and benchmarks; `daily_curves.json`, `annual_results.json`, `data_audit.json` accompany it. `test_daily.py` is import-safe; `refresh_benchmarks.py` already corrected passive benchmarks. Do not use the earlier printed whole-share, unreinvested benchmark numbers.
- At 10 bps, full 2011–2025 QLD fixed 50% trend: CAGR 12.636%, max closing drawdown 31.973%. Reserved 2022–2025: CAGR 11.873%, drawdown 19.957%, ending $3,907.23, 20 orders. Slow and violates the full-history 25% drawdown budget; not a solution.
- QQQ passive: full CAGR 18.524%, drawdown 35.119%; reserved CAGR 12.128%, drawdown 34.828%, ending $3,942.90.
- QLD overnight with trend: at 10 bps full CAGR -0.569%, reserved +1.05%. At 5 bps full +4.62%, reserved +5.58%. Strong cost sensitivity; cannot claim a robust edge. All other index variants are retained.

### New volume-shock hypothesis and completed outcome
- `volume_shock_plan.json` was frozen BEFORE downloading/examining the 37 stock daily histories. Downloads completed via `download_stock_daily.py`; 36 stocks have 4,194 rows and META 3,595 from IPO May 18, 2012. With the four ETFs, 41 histories total. Manifest `daily_raw/stock_manifest.json` contains URLs and hashes. No need to refetch.
- `test_volume_shock.py`: all frozen rules, 5- and 20-session horizons, costs 5/10/20 bps, whole shares, cash and risk constraints, gaps and stops, dividend/split handling. `volume_results/` contains 27 portfolio/benchmark summaries, all trades, full-history daily curves, annual returns, event list and audit.
- 20-session variant at 10 bps: full 2011–2025 CAGR 3.015%, drawdown 5.799%, 326 trades, ending $3,899.93. Reserved 2022–2025 CAGR 2.384%, total +9.830%, drawdown 5.134%, 81 trades, 34 winners, 56.79% stopped, ending $2,745.75. Average closing exposure 8.32%. Five-session reserved roughly flat (-$2.18). No rules were tuned after these results.
- Reserved top five trades earned $264.31 vs total $245.75. This concentration is unattractive for desired consistency. This is P&L attribution without recomputing account sizing, not a simulated 'remove winners' strategy.
- `diagnose_volume.py` is POST-RESULT attribution, not a new optimized rule. Fixed-horizon uncapitalized signal events (no stops) compared with QQQ and own group peers. Reserved 20-day 154 events: mean net 10 bps +1.8717%, 20-session block CI [-0.1986%,4.0847%]; gross peer excess -0.3882%, CI [-1.7886%,1.0538%]; gross QQQ excess +0.5686%, CI [-1.1779%,2.5870%]. 20/60-session block intervals and concentration saved `volume_results/attribution.json`. No demonstrated peer-relative edge. Do not leverage this to manufacture attractive returns.
- All cash P&L reconciles to ending equity. No held volume position crossed a split in any run. Stock corporate-action adjustment limitations remain for the historical universe/benchmark. META eligible only after sufficient history. Ex-date dividend cash is an approximation. Simulated same-open observations/fills and immediate reuse of sale proceeds require execution/account validation; account cash settlement is not modeled. Drawdown is close-to-close.
- Monthly equal-weight SAME surviving-stock benchmark at 10 bps: full CAGR 19.657%, drawdown 37.252%; reserved CAGR 18.736%, drawdown 26.502%. It illustrates selection bias but cannot remove it. Its fractional adjustment orders are not whole-share executable trades.

### Current decision and next useful research
No tested strategy meets frequent opportunities, strong returns and credible <=25% drawdown simultaneously. Do not build a bot or call any rule validated. Positive historical results are not reliable daily profits. All current periods have now been examined; future variants cannot call these untouched tests.

Possible next hypothesis: timestamped earnings surprise plus guidance increase, with a plausible persistent institutional buyer. It is NOT tested or established. Requires historical release times, figures known at the time, historical universe/delistings and executable quotes. Current analyst estimates or current calendars cannot replace historical point-in-time inputs. Keep the volume screen as a rejected baseline. Avoid repeated broad parameter searches and paid subscriptions without a concrete dataset review.

### Current broker documentation correction
Robinhood now officially documents Trading MCP and dedicated Agentic accounts supporting long equities, options and crypto. Earlier blanket 'official API is crypto-only' statements are stale. Primary sources checked this turn:
- https://robinhood.com/us/en/support/articles/agentic-trading-overview/
- https://robinhood.com/us/en/support/articles/trading-with-your-agent/
This does not verify a standalone deterministic client's support or account permissions. No account connection or trade was initiated. Robinhood documents 1-business-day cash settlement and limited margin use of unsettled proceeds; simulator does not enforce this.
- https://docs.alpaca.markets/us/docs/paper-trading : paper omissions include latency/queue effects and dividends. Paper is not validation of real execution.
- https://www.proshares.com/our-etfs/leveraged-and-inverse/qld : 2x DAILY objective, path-dependent longer holding returns.
- https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf : background on overnight drift, not our strategy's empirical validation.

### Reproduction
Use `$CODEX_PRIMARY_RUNTIME_PYTHON` for installed pandas/numpy. Run from research directory or direct script paths: `test_daily.py`, `test_volume_shock.py`, `diagnose_volume.py`, `create_research_update.py`. They use cached public data only and no trading endpoints. Normally read completed JSON instead of rerunning. `checkpoint.py --save` updates the retained Library identity/version guard in checkpoint_receipt.json. Previous checkpoint version 4 succeeded; the final save after this handoff will supersede it.
