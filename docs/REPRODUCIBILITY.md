# Reproducing and extending the research

This is an offline research archive, not a trading application. Read `AGENTS.md`, `HANDOFF.md`, `NEXT_AGENT_DIRECTION.md`, the relevant frozen plan, and saved result summaries before running a script. Failed strategies remain failed baselines. Re-running old periods does not make them untouched validation.

## Python environment

Use CPython 3.12 as the initial reproducibility baseline. The inspected Windows runtime was Python 3.12.14 with NumPy 2.3.5, pandas 3.0.1, ReportLab 4.4.9 and tzdata 2026.3. Matplotlib was not installed. These are observed environment versions, not proof of compatibility or the environment used for the original results. No backtests or package installation were run while preparing this document.

`requirements.txt` records those observed direct dependencies and leaves Matplotlib unpinned rather than inventing a version. It is not a complete transitive lockfile. A fresh installation resolves Matplotlib and transitive dependencies at installation time; record the resulting environment before claiming reproducibility. `tzdata` supplies IANA time-zone data on systems that lack it. The scripts convert data to `America/New_York`.

From the repository root, on Windows with Python 3.12 installed through a normal Python distribution:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip freeze > environment.local.txt
```

On Linux or macOS with Python 3.12 and its virtual-environment support installed:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pip freeze > environment.local.txt
```

Package installation needs internet access. Keep the environment and its generated files out of data checkpoints and version control. Prefer creating the virtual environment outside this repository until the checkpoint packaging exclusions explicitly cover `.venv`: the legacy checkpoint packager otherwise traverses most repository files.

For a non-computational dependency smoke check:

```sh
python -c "import numpy, pandas, matplotlib, reportlab; print(numpy.__version__, pandas.__version__, matplotlib.__version__, reportlab.Version)"
```

In that command and the script examples below, replace `python` with the virtual environment's Python path shown above. Do not import every project script as a smoke test: several execute work immediately on import.

## Entry points and their effects

The root scripts resolve their data paths relative to their own file, using `Path(__file__).resolve().parent`. Running from the repository root is simplest. Preserve the directory layout. Output files are generally overwritten, so use an isolated copy or review the resulting changes before accepting a replay as reproduced.

### Offline historical replays and diagnostics

- `python analyze.py`: original intraday baseline calculations, reading `raw/`, `experiment_plan.json` and `groups.json`, and writing `analysis/`. Its original rebound loop is slow; do not run it just to read completed findings.
- `python followup.py`: offline closing audit, favorable opening chronology, vectorized rebound and index-opening follow-ups. Reads the original intraday cache and writes `analysis/`. Some outputs overlap the original baseline files; preserve prior files before rerunning.
- `python portfolio_replay.py`: finite-capital replay of saved `analysis/rebound_events.json` with intraday raw prices. Writes rebound portfolio outputs to `analysis/`. Executes on import.
- `python final_diagnostics.py`: post-result intraday attribution and uncertainty calculations, reading rebound events and raw prices. Writes `analysis/rebound_enriched.json` and `analysis/final_diagnostics.json`. Executes on import.
- `python test_daily.py`: completed daily ETF experiments from `daily_raw/`; writes `daily_results/`. Despite its name this is a research experiment, not a unit-test file. It loads the four ETF histories and constructs features on import, although the full replay is protected by a main guard.
- `python refresh_benchmarks.py`: recomputes the daily buy-and-hold benchmark and rewrites existing daily results, curves and annual results. Requires existing `daily_results/` plus cached daily ETF histories. Executes on import; it does not download data.
- `python test_volume_shock.py`: completed stock daily experiment; reads the 37-stock cache, four ETF histories and `groups.json`, and writes `volume_results/`. Importing it already loads all histories and constructs events; the portfolio runs are protected by a main guard.
- `python diagnose_volume.py`: post-result volume attribution using cached prices and saved volume trades, writing `volume_results/attribution.json`. Executes on import. Its descriptive findings are not a newly reserved validation test.

For an explicitly requested reconstruction of the completed daily outputs, the dependency order is `test_daily.py`, `refresh_benchmarks.py`, `test_volume_shock.py`, `diagnose_volume.py`, then `create_research_update.py`. This is an entry-point guide, not a recommendation to rerun eliminated ideas. Saved JSON is the normal starting point.

### Network downloaders — do not run as an offline replay

- `python download_data.py`: Yahoo chart requests using rolling `60d`, `730d` and `max` windows; writes `raw/`, `groups.json` and `data_manifest.json`. It can overwrite caches with a different historical interval today. Its old `max` daily request had a documented granularity problem. It cannot recreate the original intraday snapshot merely by rerunning later.
- `python download_daily.py`: Yahoo daily ETF downloader with explicit 2010-01-01 to 2026-09-08 bounds, writing missing files in `daily_raw/` and rewriting its manifest. Existing caches are reused; reused manifest rows say `cached; see prior manifest`, so preserve the original manifest separately. Executes on import.
- `python download_stock_daily.py`: analogous daily stock downloader using `groups.json`; writes missing stock caches and rewrites `daily_raw/stock_manifest.json`. Executes on import. Fixed dates do not guarantee vendor responses have not been revised.

These downloaders use Python's standard library; no Yahoo SDK is required. A fresh Git clone may omit large cached histories. Missing files do not authorize automatic replacement: consult the archive and hash manifests first. Do not retrieve large datasets without the new experiment's frozen plan and data-feasibility gate.

`download_alpaca_via_tools.js` is an agent-tool orchestration artifact, not a root Python entry point or a guaranteed standalone Node application. It depends on a connected data-only Alpaca tool environment. The archived handoff describes repeated connector errors; a historical connection is not proof that a fresh host has access. Do not extract credentials or assume paid entitlements.

### Reports

- `python create_research_update.py`: standard-library-only rendering of saved `daily_results/results.json` and `volume_results/results.json` into `deliverables/Trading_Research_Update.md`. Executes on import. This preserves the older report's scope; it does not summarize new hypotheses automatically.
- `python create_report.py`: reads original `analysis/` outputs, generates chart PNGs under `figures/`, writes `sources.json`, and builds the original PDF under `deliverables/`. Requires NumPy, pandas, Matplotlib and ReportLab. Executes on import. It is a historical-report generator, not the current decision record, and rebuilding it does not establish visual QA or verify its embedded external references.

### Checkpoints

- `python checkpoint.py`: rebuilds the `alpaca_batches/manifest.json` hashes/counts only. It modifies that manifest even without `--save`.
- `python checkpoint.py --save`: also writes `deliverables/Trading_Research_Checkpoint.zip`. On a host without the original Linux Library helper and `/usr/bin/python3`, the current script records a local-only receipt in `checkpoint_local_receipt.json`. A local ZIP is not an uploaded Library backup or a GitHub push.

If the original helper exists at `/root/.codex/plugins/cache/openai-curated-remote/openai-library/0.1.54/skills/library/scripts/library_upload.py`, `--save` can perform a network Library upload/replacement using the retained receipt/version guard. Review the code and authorization before invoking it on such a host. Do not automatically retry an uncertain upload. This entry point executes on import and should be run only as a script.

The packager excludes selected old raw/source/figure paths and non-Markdown deliverables; its ZIP is not an exact mirror of every input in the full original archive. The manifest hashes only Alpaca batch JSON files. Keep the original full archive and its separate daily/raw manifests available for provenance.

## Cross-platform and validation limits

Old notes reference `/workspace/scratch/...`, `/root/...`, `/usr/bin/python3`, `$CODEX_PRIMARY_RUNTIME_PYTHON` and a Library plugin path. Those refer to the original environment. They are not required repository installation locations. The Windows Codex runtime used for dependency inspection was supplied by the app; a normal virtual environment is sufficient for the Python scripts once dependencies and input files are present.

The repository has no recovered original dependency lockfile and no demonstrated cross-platform numerical equivalence test. Floating-point results, timezone releases, package changes and vendor revisions can affect reproduction. Record Python/package versions, input hashes, plan hash and output hashes for any intentional rerun; compare compact numerical summaries against preserved results before accepting the rerun. Do not rename a changed output as the original result.

No script in this guide is a live execution bot. A candidate still needs realistic costs, point-in-time inputs, genuinely untouched validation, concentration analysis and 30–60 sessions of live quote or shadow-order testing before implementation can be considered. A profitable replay alone passes none of those gates.
