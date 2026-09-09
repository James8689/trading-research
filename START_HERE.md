# Start here: frontier coordinator handoff

This is James's private automated-trading **research** repository. No strategy is validated. No live orders or trading bot are authorized. The intended system is a replaceable frontier coordinator directing inexpensive workers, with persistent file-based context and evidence gates.

Read in this order:

1. `AGENTS.md` — constraints and edit ownership.
2. `research_state/state.json` if present — current task state; `research_batch3/SYNTHESIS.md` — latest scientific decision.
3. `config/agent_network.json`, `docs/AGENT_NETWORK.md` — model tiers, budgets and loop contract.
4. `research_batch3/frozen_experiment_plans.json` and its hash receipt — two feasibility plans, zero return tests.
5. `HANDOFF.md` latest appended sections; use historical sections only when needed.
6. `docs/DATA_CATALOG.md` and `docs/REPRODUCIBILITY.md` for exact existing artifacts and commands.

Do not load raw datasets or all agent conversations into your context. Each role writes compact memory and a result. Read cited evidence only when making a consequential decision. Verify file hashes and JSON before relying on result summaries. Another frontier model should be able to replace you from these files alone.

## First useful next action

Complete the frozen document feasibility probes for B3-H1-v1 and B3-M2A-v1. Both may fail their strict data gates. Do not relax gates to keep the project busy. No bulk prices or simulator until these gates pass. Other proposals and independent disagreement are retained in the batch ledger.

## Research loop

`python -m research_loop.runner --root . init` creates durable local state. `status` shows progress; `next` produces a bounded task packet. Use manual packet mode from any coding agent, or a configured CLI model runner after budget/access setup. The loop stops for blocked data, frontier review, STOP file, exhausted calls/tokens/cycles or uncertain failures. It is a resumable work queue, not a promise of eventual profitable discovery.

For deeper work: freeze source sample -> two-reader data audit -> reviewed Python extraction -> frozen experiment -> offline development -> untouched future evaluation -> concentration/cost checks -> 60-session live-quote/local-shadow evidence. The frontier agent owns the gate transitions with concrete artifacts. A worker saying "pass" is not a gate.
