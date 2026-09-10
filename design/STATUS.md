# Implementation checkpoint

Updated September 10, 2026. James authorized an operator dashboard with durable UI state and a minimal family registry around the existing manual network.

## Implemented

- `python go.py --mode dashboard`: password-protected operator UI. Gitignored `.env` can map roles to OpenAI/Anthropic/xAI models and open a local test budget from the $0 placeholder. Dispatch is one packet per request. No broker. See `docs/DASHBOARD.md`.
- `python go.py`: repeatable offline six-stage network demonstration with scripted workers.
- `python go.py --mode start`: idempotent manual CEF feasibility queue and initial versioned prompts.
- SQLite source revisions, deduplication, transactional task leases, independent-role checks, frozen packets/results, rejected-submission audit and failure recovery.
- Candidate-and-role memory history, blinded reviewer packets and bounded actionable director brief.
- Director-owned worker-prompt proposals linked to completed work; frozen baseline/challenger comparisons, fresh-suite checks, independent evaluation/review, promotion and rollback.
- Separate budget reservation/reconciliation component with no approved paid allowance, and private idle-runtime export/restore.
- Supported CLI, portable operating guide and synthetic tests. Legacy provider path disabled.

The main coding agent and internal research director are different roles. Director runtime context comes from saved artifacts, not a coding chat. Worker identities are operator labels in manual mode, not authenticated OS principals.

## Verification and current state

Fifty-four synthetic tests passed at the current implementation checkpoint; see latest HANDOFF for clean-checkout checks. The offline demo completed with zero model/broker calls and rolled back its synthetic prompt promotion. All 153 archived data files and the B3 plan hash verified. No strategy return test ran and no real prompt-quality improvement has been measured.

The local manual CEF queue is initialized with six pending tasks, no task claimed, no source evidence and six baseline prompts. This runtime state is local; a fresh checkout recreates it with `go.py --mode start`. No background process is running.

## Preserved research

B3-H1-v1 and B3-M2A-v1 remain frozen source-feasibility candidates only. Previous research failures, agent disagreement and external-claim reviews remain recorded. Read research_batch3/SYNTHESIS.md. Nothing in the controller promotes a strategy to live use.

## Remaining boundary

Latest design correction: EVIDENCE_LED_DEVELOPMENT.md prioritizes a minimal family registry and one real manual document-feasibility cycle before architectural expansion. It specifies recurring-pattern evidence, substantive evaluation and probation for adaptation, plus independent builder feasibility review before blueprint readiness. These additional gates are not yet runtime-enforced. The earlier broad roadmap is now sequenced around observed bottlenecks.

Latest mission direction: read OPPORTUNITY_ENGINE.md. The engine should explore broadly, preserve semantic idea-family history, learn through memory/prompts/routing, and deliver validated blueprints to a separate production builder. The preferred diverse model stack is recorded as configuration intent, not verified adapters. Next build priority is the canonical mission/portfolio and opportunity-family/blueprint contracts around existing gates. Automatic provider execution remains necessary later; the broader loop is not implemented yet.

Automatic provider execution is a bounded, operator-triggered adapter (`/dispatch` or Mission/Spend). It is not an unattended loop. The legacy `research_loop/runner.py` path stays disabled. Evaluation labels are withheld from packets but readable to a same-user process; do not claim technically sealed holdouts.

Resume from START_HERE.md and docs/ORCHESTRATION.md. Use the manual queue or implement the next explicitly scoped provider component; do not resume the obsolete runner or silently spend money. Save and push completed batches to the private GitHub repo.
