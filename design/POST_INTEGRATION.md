# September 9: external posts and design integration

Status: design changes only. No runtime, strategy rules, provider configuration or frozen experiment changed.

## Sources and limits

James supplied [Roan's post](https://x.com/rohonchain/status/2097303933081489605) and [sopersone's post](https://x.com/sopersone/status/2095105287061721111). Direct X retrieval returned 403. Article text and embedded code were retrieved September 9, 2026 through the public FxTwitter API at the corresponding `/status/` paths. This is mirror provenance, not independent authentication or replication. Images were not used as evidence. No source code from either article was executed.

Roan describes a scanning, hypothesis, backtest, validation, risk and notification pipeline. Its sample passes candidates through fixed statistical thresholds and emits confidence percentages. It proposes executing generated entry/exit code. Its model specifications, pricing, institutional comparisons and profitability claims are unverified here. Useful overlap: separate inexpensive intake from expensive research and independent validation. The article is a design proposal, not a reproducible net-return record.

sopersone describes service-selling agents with separate treasury, work and lifecycle responsibilities, spending limits and failure journals. The article explicitly prohibits trading. It reports population outcomes but defers full financial logs. Useful overlap: independent resource enforcement, bounded capacity and retained failure history. Its economic experiment does not establish trading alpha or secure isolation; different role names on a shared host are not proof of separate permissions.

## Project decisions

The following are our proposed engineering requirements, not verified capabilities of the articles or current runner.

### 1. Add deterministic evidence intake before research dispatch

Place this between source adapters and the existing scout/data roles in NETWORK.md. Begin with the two frozen B3 candidates' document sources, rather than expanding the asset universe. An intake adapter records source URL, publication time, first-observed time, retrieval time, content hash, instrument identity and candidate family. Unknown publication time remains null; ingestion time cannot substitute for knowledge time.

Use an append-only event queue with idempotent ingestion and bounded capacity. A source revision becomes a new linked version. Deduplication cannot discard materially different evidence. The controller dispatches only ready, authorized packets; an unchanged source triggers no model call. Historical document discovery does not become an immediate trade signal.

Acceptance: ingest the same document twice and produce one ready event; ingest a revision and preserve both hashes; simulate two writers without lost events; preserve stale/missing-time events as blocked; restart without duplicate dispatch. Quote feeds belong to the later shadow stage, after scientific gates.

### 2. Make budget enforcement an external controller responsibility

Extend COST_AND_SCHEDULING.md with a controller-owned reservation ledger. Research workers cannot change caps, pricing records, admission logic or the stop mechanism. Research funding stays separate from brokerage balances and strategy returns. No wallet or fund-sweeping subsystem is needed.

Expose remaining approved resources, pending reservations and unknown charges to the director. Estimated time remaining is informational and requires measured usage; unknown burn is not infinite runway. When funds are insufficient, checkpoint and pause. Do not reduce validation standards or switch to an uncalibrated model to squeeze in another task.

Acceptance: simultaneous requests cannot overspend the unreserved balance; restart retains reservations; a timeout keeps an unresolved charge; worker attempts to alter policy fail at the permission boundary; pausing preserves evidence and resumes without duplicate calls. Test these with fake provider debits before real spending.

### 3. Preserve every attempt and its ancestry

Extend RESEARCH_LIFECYCLE.md with parent candidate/version, changed fields, reason for change, source evidence, outcome windows already viewed, resource usage, decision and reopening condition. Generate concise lessons from retained records, with links to the underlying evidence. Distinguish scientific rejection, unavailable data, insufficient evidence and budget pause.

A modified candidate is a new registered trial in the same campaign where appropriate. Changing one parameter improves traceability but does not establish causality or statistical independence. No automatic population growth or profit-funded spawning. Adaptive development never inherits the label of untouched validation from its parent.

Acceptance: a child using a viewed outcome period cannot call it a fresh holdout; failed/paused attempts remain in reports; no repeated failed family is dispatched without new reopening evidence; child tasks consume the central concurrency and resource limits.

### 4. Keep notifications downstream of evidence

Use the existing gate/result packets for a later status interface: candidate version, stage, evidence links, blocker, resource use and next decision. A model-generated confidence percentage is not a measured probability of profit. No new Telegram integration is needed for this design batch. Future delivery needs an event/version outbox and uncertain-send reconciliation, not only a strategy-ID sent flag.

## What stays out

Do not adopt the articles' role counts, subscriptions, model prices, generic strategy templates, survival objective, replication rules or statistical thresholds as project defaults. Do not execute free-text hypothesis code automatically. Any later simulator implementation requires code review and isolated tests. Continued search needs campaign-wide trial accounting and independent future confirmation; isolated Sharpe or t-statistic cutoffs cannot substitute for those gates.

## Ordered next steps

1. Review these requirements alongside IMPLEMENTATION_HANDOFF.md; use synthetic fixtures for queue, reservation and recovery acceptance before a provider adapter.
2. Resolve research spending/billing preference before enabling paid unattended dispatch. The Robinhood account's $10 is not an inference budget.
3. When source research resumes, perform the existing frozen document probes for B3-H1-v1 and B3-M2A-v1. Preserve negative results and missing fields. Do not broaden to new strategy families merely because a post lists them.
4. Measure whether a separate intake worker improves useful evidence per cost before adding more workers or providers.

Session context correction: Robinhood read-only account, portfolio and position calls succeeded in this conversation. That verifies this session's connector access only; the repository still has no tested broker adapter or execution system.
