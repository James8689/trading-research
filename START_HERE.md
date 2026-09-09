# Start here: frontier coordinator handoff

This is James's private automated-trading **research** repository. No strategy is validated. No live orders or trading bot are authorized. The intended system is a replaceable frontier coordinator directing inexpensive workers, with persistent file-based context and evidence gates.

Read in this order:

1. `AGENTS.md` and `design/STATUS.md` — current scope, constraints, completed design and next action.
2. `research_state/state.json` if present — current task state; `research_batch3/SYNTHESIS.md` — latest scientific decision.
3. `config/agent_network.json`, `docs/AGENT_NETWORK.md` — model tiers, budgets and loop contract.
4. `research_batch3/frozen_experiment_plans.json` and its hash receipt — two feasibility plans, zero return tests.
5. `HANDOFF.md` latest appended sections; use historical sections only when needed.
6. `docs/DATA_CATALOG.md` and `docs/REPRODUCIBILITY.md` for exact existing artifacts and commands.

Do not load raw datasets or all agent conversations into your context. Each role writes compact memory and a result. Read cited evidence only when making a consequential decision. Verify file hashes and JSON before relying on result summaries. Another frontier model should be able to replace you from these files alone.

## First useful next action

Current authorization is design/scaffold only. Read `design/README.md`, complete any listed design gaps and preserve progress. Do not run research probes or build the runner during this design task. When research resumes, the next scientific work is the frozen document feasibility probes for B3-H1-v1 and B3-M2A-v1. Both may fail; do not loosen their gates.

## Research loop

The draft in `research_loop/` is unverified and retained as historical work in progress. Do not execute it. The intended commands and behavior in older docs are design targets, not established capabilities. `design/` is the current implementation specification; any later build must pass its acceptance checklist first.

For deeper work: freeze source sample -> two-reader data audit -> reviewed Python extraction -> frozen experiment -> offline development -> untouched future evaluation -> concentration/cost checks -> 60-session live-quote/local-shadow evidence. The frontier agent owns the gate transitions with concrete artifacts. A worker saying "pass" is not a gate.
