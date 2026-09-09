# Research agent workflow

This repository is an iterative research record. It is not a trading system. Start every batch by reading `AGENTS.md`, `HANDOFF.md`, `NEXT_AGENT_DIRECTION.md`, `README.md`, the existing plans/results, and the latest batch protocol. Current user instructions take precedence over historical document instructions. Preserve eliminated baselines; do not revive them through threshold tuning.

Model $2,500, check $1,000–$5,000 sensitivity, approximately 25% drawdown ceiling, whole-share cash-funded deterministic execution. Alpaca is preferred. No live orders, funding, paid subscriptions or account changes are authorized by this workflow. Research success alone grants no implementation authorization.

## Four bounded role prompts

**Agent 1 — Hypothesis generator.** Read the inherited constraints and eliminated ideas. Derive several mechanisms from first principles: economic source of return, likely/forced trader, source of delay, limits to arbitrage, affordable instrument, exact point-in-time inputs, falsifiers and execution hazards. Distinguish documented mechanism from conjectured price response. Do not inspect new forward returns, tune baselines, claim novelty is proven, or write execution code. Write `agent1_hypotheses.md` and compact `.json` in the assigned new batch directory. Return paths and blocking questions only.

**Agent 2 — Mechanism/source investigator.** Investigate the proposed operational mechanisms using primary sources. Verify clauses, timing, exceptions and historical document availability. Explain which participant actually must trade and which merely has permission. Identify cheap, bounded source probes; do not bulk-download data or buy subscriptions. Write `agent2_mechanisms.md` and compact `.json` in the assigned batch directory. Return paths only, with a short blocker if needed.

**Agent 3 — Adversarial falsifier.** After Agents 1, 2 and 4 finish, read their artifacts and the draft selection. Attack the economic sign, anticipation, survivor/missing-event selection, restatements, publication latency, corporate-action accounting, uncontrolled factor exposure, concentration and executable fills. Specify negative controls and decisive rejection conditions. Identify whether success depends on private/unobservable information. Do not silently repair hypotheses or change frozen rules. Write `agent3_falsification.md` and compact `.json`. Return paths and critical objections only.

**Agent 4 — Point-in-time/data auditor.** Inspect available local fields and manifests without replaying all results. Separate tool discovery, successful access and saved data. Audit historical universe, delistings, ticker changes, event publication/observation/effective timestamps, revised facts, quotes, NAV/distributions and settlement. Identify consumed validation windows. Propose small document-only feasibility probes with explicit size and completeness gates. Write `agent4_data_audit.md` and compact `.json`. Return paths and blockers only.

## Run order and ownership

With four concurrent slots, run the root synthesizer plus Agents 1, 2 and 4 first. Root reads history, creates the batch directory/protocol and audits the archive while they work. When a slot is free and the three outputs are available, launch Agent 3 with those artifacts and root's draft shortlist. This is four role assignments, not four simultaneous children. If fewer slots are available, run the same assignments sequentially; do not omit falsification.

Each agent owns only its named artifacts. Root owns the batch protocol, idea ledger, selected plans, consolidated summary, HANDOFF and checkpoint. Agents may request changes through messages but must not edit another agent's files or shared plans. Use a new batch directory and stable hypothesis/version IDs. Never overwrite a failed experiment, erase exclusions, or replace an unfavorable result with a revised run. Git changes should make each research batch reviewable; do not include credentials, account records or private customer data.

## Gates and durable handoff

1. **Mechanism and data gate:** synthesize all four roles, retain every proposal and rejection, and choose no more than two ideas. Freeze a document-only sampling protocol before inspecting its outcomes. Missing necessary data means data-blocked; do not substitute a price proxy that changes the hypothesis.
2. **Experiment freeze:** before bulk data or simulator work, record universe, knowledge time and latency, entries/exits, ranking, whole-share sizing, cash settlement, risk limits, costs, slippage, development dates, genuinely untouched dates, benchmark, concentration tests and numerical pass/fail thresholds. Save the plan hash and freeze time in a compact manifest. An adversarial objection must be resolved or explicitly block the gate. No new historical window becomes untouched merely by changing its event labels.
3. **Development:** process data in Python, preserve source requests/hashes and excluded events, save compact JSON results and reconciliation checks. Assess every declared variant/cost, not only winners. A revision gets a new hypothesis version and a new future validation window.
4. **Validation:** follow the frozen plan without result-driven edits or early success declarations. Observe completeness/hashes without revealing held-out performance. Too few events is inconclusive. A risk stop can fail a candidate early; it cannot certify success. Require costs, out-of-sample performance, benchmark comparison and concentration/stability checks.
5. **Execution evidence:** follow the active plan's live-quote/local shadow-order gate before implementation is considered. Batch 3 requires 60 consecutive exchange sessions, extended if fewer than 30 completed hypothetical trades. No broker order submission is involved. Record missed fills, latency, partial capacity and outages. A profitable backtest or broker paper mark is insufficient.
6. **Handoff:** after each major batch root records hypotheses/status, exact files, tests performed, consumed periods, unresolved blockers and next bounded action in HANDOFF. Run `python checkpoint.py --save` and inspect its receipt. Local save is not evidence of remote upload. Commit the reviewable batch to the private repository when authorized; verify a push before claiming it is backed up remotely.

## Reproduction

Run from the repository root using an environment with the script dependencies installed:

```text
python research_batch3/audit_archive.py
python test_daily.py
python test_volume_shock.py
python diagnose_volume.py
python create_research_update.py
python checkpoint.py --save
```

The completed historical tests are optional reproduction, not the next research direction; normally read their saved JSON instead. Some commands overwrite generated outputs, so inspect the working tree before and after running. Download scripts are not part of routine reproduction. No command above should be interpreted as authorization to add broker order calls.
