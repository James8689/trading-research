# Proposed post-inspired integration: acceptance review

September 9, 2026. Design review only, against `COST_AND_SCHEDULING.md` and `RESEARCH_LIFECYCLE.md`. These are proposed architectural adaptations of external posts, not verified implementations or validated performance. This review does not independently establish what either post says. No runner, model call, strategy freeze, or trading permission changes.

## 1. Deterministic source-event queue before LLM research

**Existing coverage:** scheduling already requires ready tasks, dependencies, authority and budget; empty polling must not invoke models. Feasibility requires a predeclared source sample and missing-field denominator. Frozen plans include the source protocol and knowledge clock.

**Gap:** neither document specifies event identity, source revisions, durable deduplication, replay behavior, or how deterministic source screening creates eligible research tasks.

Acceptance criteria for a future implementation:

- Persist a source envelope before dispatch: source ID/URI, stable event key, source publication time when known, first-observed and ingestion times, raw-content hash, revision relation, parser/schema version, candidate/version, and applicability decision with reason. Unknown times remain unknown and block time-critical eligibility when required.
- Version deterministic filters for source allowlist, event type, required fields, freshness and candidate scope. Missing or malformed records enter a quarantine with reasons; they remain in coverage denominators. Screening cannot use subsequent prices, realized returns, or outcome-based ranking.
- Repeated receipt of the same event/revision creates no duplicate research admission or charge. A content revision creates a linked version, preserves the original, and uses its own knowledge time; it cannot retroactively improve historical inputs.
- Queue state and leases survive crashes. Replay reproduces eligibility and ordering from the same input snapshot/configuration. In-flight uncertain calls require reconciliation before retry; deduplication alone cannot guarantee exactly-once external execution.
- Deterministic extraction completes fields it can establish; a model is admitted only for a registered unresolved question with a decision it can change, effort cap and stop condition. An empty queue and events rejected by deterministic filters cause zero model calls.

Suggested acceptance scenarios: duplicate delivery; revised filing; late arrival; missing timestamp; malformed payload; crash after dispatch; empty source poll. Verify preserved evidence, coverage counts and call admission in each.

## 2. External budget controller, pause/resume and all-attempt lineage

**Existing coverage:** the cost specification already requires an exogenous approved budget, reservations, unknown-charge handling, reliable pricing, period identifiers, finite run bounds, immediate STOP, and accounting that survives resume. The lifecycle already calls for all explored variants and viewed outcome windows in a global ledger.

**Gap:** enforcement ownership, atomic admission, durable request states, reconciliation identity, and the join between model attempts and scientific trials are unspecified. Text instructions to a worker are not an enforceable budget boundary.

Acceptance criteria for a future implementation:

- A controller outside model-authored policy owns dispatch and a durable monetary/usage ledger. Model output cannot change limits, pricing, period boundaries, permissions or STOP state. No approved budget/access mode means no automatic admission.
- Atomically reserve worst permitted charges before dispatch, including explicitly bounded tools. Concurrent workers cannot each spend the same remaining balance. Unknown or uncappable charges prevent a hard-dollar guarantee and block the affected automatic path.
- Give every admission and attempt immutable IDs linked to run, task, parent/retry, source event, candidate/version, prompt/model/config hashes, reservation, provider request ID when available, usage, terminal state and resulting artifact hashes. Record failures, cancellations, rejected output, repairs and uncertain timeouts; do not count only accepted results.
- Keep a scientific trial ledger distinct from the billing ledger but link them. Clerical retries are not automatically distinct strategy trials; strategy mutations and viewed outcome windows remain registered even if a call fails or a candidate is discarded.
- STOP atomically blocks new admissions. Preserve and reconcile in-flight work; a timeout is not evidence of zero cost. Resume restores outstanding reservations and consumed limits without a fresh allowance. Period rollover follows the declared boundary and retains unresolved liabilities under a documented allocation policy.
- Report actual, estimated, reserved and unknown costs separately. Reconciliation records are append-only corrections, with no untraceable rewriting of prior attempts.

Suggested acceptance scenarios: simultaneous last-budget requests; crash after reservation; provider timeout with later charge; duplicate billing receipt; repair attempt; process restart; STOP during dispatch; period rollover with unresolved usage. Each must preserve lineage and prevent unaccounted new spending.

## 3. Adaptive strategy mutations and holdout contamination

**Existing coverage:** the lifecycle freezes rules before outcomes, preserves every variant, requires independent custody, explicitly admits the current procedural barrier is not technically sealed, prohibits confirmation-window reuse, and treats corrections as potential contamination. These policies already reject adaptive tuning on a holdout.

**Gap:** no implementable access contract, mutation boundary, feedback whitelist, holdout-consumption transaction or leakage-response record is specified.

Acceptance criteria for a future implementation:

- Register each mutation as a new linked strategy version before its outcomes are acquired. Freeze the full decision pipeline, including source selection/extraction prompts, model/configuration, universe, rules, controls, costs, stopping rule and primary metric. Preserve the previous freeze and its decision.
- Tuning workers can access development data only. A separate custodian identity/storage boundary protects reserved outcomes and derived artifacts, logs, caches and summaries. Until enforced and verified, retain the label "protected by procedure," not "sealed."
- Define and freeze an allowed metadata interface before reservation. Completeness/latency feedback must not reveal outcome-dependent inclusion, fills, profitability, rankings or candidate comparisons. Repeated metadata queries cannot become an indirect optimization channel.
- A release transaction checks frozen hashes, authority, scheduled release and unused-window status, then permanently records the evaluated version and consumed window. A failed or interrupted release is reconciled before another evaluation; it cannot silently produce repeated chances at confirmation.
- Any mutation informed by released results returns to development and needs genuinely untouched future confirmation under predeclared campaign-wide error control. It cannot inherit the parent version's confirmatory status or recycle the inspected window.
- On accidental exposure, stop affected advancement, record who accessed which window/artifact and when, mark the window consumed or contaminated for affected tuning paths, preserve findings as exploratory, and reserve fresh confirmation if the candidate continues. Bug corrections preserve old results and disclose contamination.

Suggested acceptance scenarios: changed prompt with unchanged strategy name; holdout summary in a worker log; model-cache reuse; outcome-dependent coverage feedback; two versions seeking the same release; restart after partial release; bug discovered after evaluation. None may silently preserve an untouched-holdout claim.

## Integration order

First specify the deterministic event schema and admission contract; then specify durable controller enforcement and linked ledgers; then establish verified holdout access separation before any reserved validation. Keep all automatic calls disabled pending spending/access authorization and a separate implementation request. These adaptations improve auditability and experimental discipline; they do not establish an edge, expected profit or permission to trade.
