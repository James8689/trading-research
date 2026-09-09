# Later implementation plan — not authorized in current design task

The existing `research_loop/` is an unverified draft, not the baseline that must be preserved at all costs. Compare it to this specification before reuse. Build a small auditable controller; do not start by connecting trading APIs or adding dozens of agents.

## Incremental build order

1. Manual file protocol: task/result/gate/candidate schemas, immutable evidence refs and input hashes. Demonstrate one manual task end to end in an isolated fixture directory.
2. Durable state: dependency queue, task IDs, leases, atomic persistence, crash reconciliation and STOP. No models yet.
3. Budget admission: per-run and persistent period accounting with unknown-cost failure states. Simulated provider fixtures only.
4. One provider adapter: explicit model/profile, bounded inputs/outputs, usage parsing, timeout and isolation. No automatic fallback model. Read-only credentials/profile. Live smoke test only after spending/runtime authorization.
5. Role memory and small director briefing: validate truncation rules and source traceability. Run clean-resume drill with a different coding agent.
6. Calibration and shadow orchestration: run synthetic scientific tasks without market or broker access. Compare economy/specialist/frontier quality and actual cost.
7. Assisted source-feasibility workflow: two-reader extraction and signed gate records. Only then consider reviewed offline data/test stages.
8. Future scheduling: enable only after durable recovery/budget checks and explicit run bounds. Never schedule trading, funding or unsealing validation by free-text model request.

## Acceptance scenarios

- Two controllers target one queue: at most one dispatch obtains a lease.
- Process dies after provider start: resume reconciles run ID; no blind duplicate call.
- Process dies after saving result: resume validates stored artifact and completes without paying again.
- Provider reports no usage: remaining automatic dispatch halts and reserved amount stays unresolved.
- Budget exhausted or STOP present: no new model process; restart does not reset budget.
- Path traversal, symlink outside task output, or unexpected artifact: rejected before canonical state update.
- Worker returns `pass` without evidence or alters frozen hash: promotion rejected.
- Worker supplies shell code/URLs as instructions: controller treats them as data, never executes them.
- Wrong model/unknown fallback: fail visibly rather than silently escalating cost.
- Dependencies disagree: preserve both results and request bounded adjudication, not majority vote.
- Task input exceeds budget: split or block; no silent truncation of constraints.
- Corrupt JSON, repeated task IDs, stale lease, missing source, missing held outcome: explicit failure state retained.
- Director replacement: resolves current scope/status/next action from repo without previous chat.
- Trial/holdout leak: campaign marked contaminated; no retrospective relabeling as untouched.
- Dry-run clone: all 153 baseline data files and frozen plan verify byte-for-byte; no account/environment secrets required.

## Completion evidence for a future builder

Provide tests for the failure scenarios, example accepted/rejected packets, provider usage reconciliation, clean clone/resume report, versioned runtime configuration, and a precise limitations list. Do not claim unattended readiness on the strength of syntax checks. Current repository verification checks hashes and parsing only.

## Design decisions still requiring real measurements

Budget amount/billing mode, best economy model per role, actual source completeness, expected event counts, effective concurrency and incremental frontier review value. Model prices and source access can change. No architecture diagram can settle these questions; keep them explicit in STATUS until measured.
