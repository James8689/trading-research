# Trading research

Start with [START_HERE.md](START_HERE.md). This private repository preserves the complete imported research history, cached backtesting data, scripts, rejected strategies, new hypotheses and agent-network design.

**Current build status:** research documents and two feasibility plans are frozen. The agent-loop implementation is a draft: its worker was interrupted by a usage limit before testing was completed. It is not ready for unattended use. Automatic model calls remain disabled. No strategy is validated and no live trading is authorized.

- [Agent network](docs/AGENT_NETWORK.md): replaceable frontier director, cheaper workers, isolated context and bounded work.
- [Reproduction](docs/REPRODUCIBILITY.md) and [data catalog](docs/DATA_CATALOG.md).
- [Latest research synthesis](research_batch3/SYNTHESIS.md) and [frozen plans](research_batch3/frozen_experiment_plans.json).
- [Model evaluation](docs/MODEL_EVALUATION.md): calibration fixtures, not measured model performance.

The `research_loop/` commands described in the design are provisional until tests and runtime review pass. Do not launch paid/background runs from this draft.

This repository contains the preserved research for James's automated trading project. It is an offline research archive and does not submit brokerage orders.

Start with [`HANDOFF.md`](HANDOFF.md), then read [`NEXT_AGENT_DIRECTION.md`](NEXT_AGENT_DIRECTION.md). Existing experiments and results are retained in `analysis/`, `daily_results/`, and `volume_results/`. Cached histories and their manifests are in `daily_raw/`. Use the installed Python runtime to run scripts only when a reproducible rerun is needed.

The current decision is that no tested rule is ready for live money. The next pass should use creative, first-principles hypothesis generation and rigorous falsification rather than repeatedly optimizing known strategies.
