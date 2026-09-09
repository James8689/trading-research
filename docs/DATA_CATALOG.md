# Data and artifact catalog

Paths below are relative to the repository root. Existing files remain in their original locations. This catalog does not claim a complete point-in-time market database or validated strategy. Read `HANDOFF.md` for decisions and the latest batch for prospective plans.

## Inputs and provenance

- `raw/`: original vendor responses used for early intraday experiments. `data_manifest.json` records the original collection. These are bars, not executable quotes. Preserve request metadata and examine actual coverage before reusing them.
- `daily_raw/`: cached Yahoo responses for 37 surviving stocks plus SPY, QQQ, SSO and QLD. `manifest.json` covers ETF downloads; `stock_manifest.json` covers stocks. Response fields include timestamps, OHLCV/adjusted prices and dividend/split events. Most histories have 4,194 rows from January 2010 through September 4, 2026; META starts at its 2012 IPO. Corporate-action records are not original publication-time records.
- `alpaca_batches/2020-01_semiconductors.json`: preserved six-symbol January 2020 five-minute batch, 17,643 bars including extended hours. Contains request, counts, column names and compact bar arrays. `calendar_2020.json` is the saved calendar. `manifest.json` records files, counts, requests and hashes. Only manifest-backed completed files count as downloaded; failed requests do not.
- `groups.json`: fixed 37-stock/seven-group research universe, selected from surviving stocks. It is not a historical membership database.
- `sources/`: historical supporting source artifacts. Check publication dates and document versions before using them as rules. Current rules or web pages do not prove historical knowledge.

There is no verified saved historical quote dataset for the new mechanisms. The historical handoff mentions a successful Alpaca quote probe; currently discoverable tools and historical access reports do not prove working access today. No credentials are needed for archive reproduction. Do not extract or store broker secrets.

## Frozen plans and completed results

- `experiment_plan.json`, `followup_plan.json`, `portfolio_plan.json`: early intraday designs and fixed-capital follow-ups. `analysis/` preserves rebound, closing momentum, opening breakout, portfolio and diagnostic summaries. These are rejected or benchmark baselines.
- `alpaca_extension_plan.json`: frozen unchanged-baseline extension, with original 2020–2023 diagnostic and 2024–2025 reserved labels. Download/access failures prevented completion of the planned extension. Those old labels do not make dates untouched for new research.
- `daily_experiment_plan.json`: daily ETF overnight and trend comparators. `daily_results/` contains `results.json`, curves, annual results and data audit. Corrected passive benchmarks are already saved; preserve them.
- `volume_shock_plan.json`: rejected company-information proxy tested with five- and twenty-session exits. `volume_results/` preserves portfolio/benchmark results, trades, curves, event list, data audit and attribution. Positive aggregate return did not establish peer-relative alpha and was concentrated in a few winners.
- `research_batch3/`: mechanism generation, primary-source audit, adversarial findings, data feasibility, frozen successor plans and compact summaries as they are completed. Its protocol treats prior history as development context. A plan in this directory is not a result.
- `deliverables/Trading_Research_Update.md`: current historical-results narrative generated from saved JSON. Original PDF and reports are historical; do not claim the unfinished workbook or full original visual QA was completed.
- `figures/`: generated historical charts. These are presentation outputs, not additional market data.

## Scripts

- `download_data.py`, `download_daily.py`, `download_stock_daily.py`: historical data collectors. Do not rerun by default; read manifests and use cached files first.
- `download_alpaca_via_tools.js`: prior resumable connector download orchestration. Requires the described app/tool environment; it is not a portable stand-alone Python script. Historical connector errors require a tiny successful probe before any batch loop resumes.
- `analyze.py`: original intraday analysis; its main rebound loop can be slow. `followup.py` includes faster event logic. `portfolio_replay.py` performs the fixed-capital replay. `final_diagnostics.py` contains further historical diagnostics.
- `test_daily.py`: completed daily ETF tests. `refresh_benchmarks.py`: corrected passive benchmark calculations; do not revert to older unreinvested/whole-share benchmark numbers.
- `test_volume_shock.py`: completed frozen volume-event tests. `diagnose_volume.py`: post-result attribution, not a newly validated rule.
- `create_research_update.py`: regenerates the Markdown update from results. `create_report.py`: original report generation.
- `research_batch3/audit_archive.py`: compact archive inventory/integrity audit. Read its summary instead of printing raw histories.
- `checkpoint.py`: updates saved Alpaca manifest and, with `--save`, builds a checkpoint ZIP. On this Windows host the historical Linux Library helper is unavailable; local receipt explicitly distinguishes local save from remote persistence. The ZIP omits original `raw/`, `sources/`, `figures/` and binary deliverables, so it is not a full substitute for the original archive or a complete repository backup.

## Reproduce only when needed

Use Python with pandas/numpy and any script-specific requirements installed, from the repository root. Read saved summaries first. For an intentional replay:

```text
python test_daily.py
python test_volume_shock.py
python diagnose_volume.py
python create_research_update.py
```

These regenerate historical outputs; inspect diffs and retain provenance. For inventory and a local checkpoint:

```text
python research_batch3/audit_archive.py
python checkpoint.py --save
```

## Known limitations and validation boundary

All previously observed history through September 8, 2026 is development context for new ideas. Prior 2022–2025 and 2024–2025 reserved periods are consumed. Follow the new frozen plan for genuinely prospective validation; do not move dates after examining outcomes.

Missing capabilities include a complete historical investable universe with delistings, original event/announcement observation times, amendment lineage, fund-specific historical DRIP routing, reinvestment participation, and executable quote coverage. Daily bars cannot resolve intraday ordering or prove fills. Revised adjusted prices require careful nominal-share accounting. Ex-date dividend cash is an approximation in older tests; payment-date settlement and restricted cash need explicit modeling in successors. Whole-share cash constraints, spreads, fees, latency, missing outcomes, concentration and gap losses can erase small apparent edges. No candidate is approved for live capital.
