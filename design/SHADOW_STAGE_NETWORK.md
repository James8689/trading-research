# Future shadow-stage network

This is a role scaffold for **live data observation and hypothetical orders only** after a strategy passes frozen historical and prospective validation gates. It is not authorized to trade, connect a funded account or execute now.

## Roles

**Opportunity observer:** consumes only the frozen deterministic signal and approved point-in-time sources. Emits candidate ID, timestamp, raw evidence references and expiry. It cannot size or approve.

**Data sentinel:** verifies source age, symbol/contract identity, venue state, corporate actions, missing fields and conflicting feeds. Any unresolved identity/timestamp issue blocks the observation. It cannot reinterpret the signal to make it pass.

**Market-liquidity sentinel:** records current spread, valid quote age, displayed depth, recent trade conditions, halt status and conservative exit capacity. It owns a binding veto. Reconsideration requires a new observation after explicit market conditions change; a price increase alone never overrides the veto.

**Signal verifier:** recomputes the frozen rule deterministically from source artifacts. Its output is pass/fail plus exact calculation. An AI narrative cannot replace the calculation.

**Alternative-explanation reviewer:** checks scheduled news, market-wide moves, data revisions and known confounds. This role can mark the event non-evaluable; it cannot invent an extra filter after seeing outcome.

**Risk allocator:** applies account equity, whole-share cash, correlation/group caps, settled cash, modeled gap loss, maximum safe notional and drawdown halt. It can reduce to zero; it cannot increase limits because a signal is persuasive.

**Hypothetical execution planner:** creates a local order intent with limit, latency, expiry, cancel/reprice policy and exit logic. No broker submission capability. It consumes approval tokens from required roles and rejects stale approvals.

**Execution observer:** compares the intent with subsequent quotes/trades to estimate whether the hypothetical order could have filled. It records no-fill, partial capacity and adverse movement. Quotes do not prove a fill.

**Ledger/reconciler:** maintains hypothetical cash, positions, entitlements, costs and marked/liquidation equity. It reconciles independently of strategy claims and never fills gaps with favorable prices.

**Session director:** assembles signed role outputs, preserves vetoes and writes a report. It cannot override risk/data blocks or convert a shadow record into a live order. It escalates discrepancies to a frontier reviewer.

## Handoff contract

Each message contains strategy/candidate version, event ID, observation and expiry timestamps, input artifact hashes, status, evidence, calculation, uncertainty, veto/reopening condition and output hash. Approvals expire when the quote, source, strategy hash or account snapshot changes. Downstream roles consume files, not prose copied from a chat.

Use deterministic code for signal, risk, order arithmetic and ledger. Economy models may summarize/check bounded evidence after calibration. The frontier model handles ambiguous identity, conflicting evidence and experiment-level decisions; it does not make discretionary trade calls. No role can add a new feature or threshold during shadow observation.

## Veto semantics

`BLOCKED_DATA`, `BLOCKED_LIQUIDITY`, `BLOCKED_RISK`, `EXPIRED`, `NO_FILL` and `EVALUABLE` are distinct. A blocked event is retained in the denominator. A later eligible event gets a new ID linked to the original and must repeat every required check. The system must report the opportunity cost of vetoes without training itself to override them after favorable price moves.

## Performance accounting

Report every eligible observation, veto, hypothetical intent, no-fill and exit. Net results include spread, latency movement, missed fills, model/data/compute cost and cash settlement. Ending marks use executable bid capacity or are flagged unresolved. Success requires the active frozen plan's number of sessions/trades, cost stress, drawdown, concentration and untouched validation gates. One dramatic session cannot advance a strategy.

