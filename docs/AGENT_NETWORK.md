# Research network and operating loop

The director should spend its context and budget on disputed mechanisms, experiment design and evidence decisions. Narrow workers handle source inspection, structured extraction and falsification. More workers are useful only when their independent information exceeds their coordination and review cost. Start small and measure it.

## Proposed orchestration — not operational

Design target: Python owns durable task state, bounded dispatch, schema checks and result/memory files. A cycle is scout -> mechanism/data -> adversary -> frontier coordinator. Each worker receives a fresh bounded context. The existing implementation is an untested draft, interrupted by a usage limit. Manual packet and CLI behavior below are intended contracts, not verified functionality. Current user scope is instructions and scaffolding only; `design/README.md` is the expanded specification.

Each result contains summary, decision, evidence, uncertainty, next_action and memory. Individual results are retained; memory is a lossy index, never a substitute for source evidence. A model swap changes configuration, not research rules. Model names in the initial config match this session's exposed model options; availability and actual billing must be reverified on another host. No price savings have been measured yet.

The initial worker is gpt-5.6-luna and director gpt-6-astra. These are interchangeable defaults, not a claim of optimality. Calibration tasks in `evals/` measure critical misses and cost per correctly completed task. Promote a cheap worker's task to a stronger model when it cannot locate evidence, produces invalid output, or fails the calibration gate; preserve its failed attempt. Do not blindly retry or have workers spawn workers. Fan-out and retries consume one centrally tracked budget.

## Scientific lifecycle beyond ideation

The intended v1 loop covers bounded research reasoning and review handoff. There is no verified runnable loop. Source acquisition, simulators, holdout evaluation and strategy promotion require separate frontier coding-agent stages and artifact checks:

- Proposal -> source feasibility: mechanism, timestamps, cheap expression and smallest falsifier.
- Feasibility -> frozen experiment: original documents, two independent extractions, exclusion ledger and exact fields; then hash the rule specification.
- Frozen -> development: reviewed Python, data hashes, cost/settlement/adjustment tests, all declared outcomes retained.
- Development -> reserved evaluation: immutable rules and future window, no interim success inspection.
- Evaluation -> quote study: costs, uncertainty, concentration, event count and drawdown pass; local hypothetical fills only.
- Quote study -> implementation consideration: at least 60 sessions plus sufficient hypothetical trades; James's original no-live-trading instruction remains.

Every stage can reject, become inconclusive, or block. Reopening requires new evidence and a new version. The goal is useful falsification per dollar, not task counts or a never-ending loop that manufactures a winner.

## Budget and failures

Defaults bound a run to two cycles, 12 calls and 120,000 reported tokens, with 300 seconds per call. Automatic calls are initially disabled. CLI token usage is post-call telemetry; a call/time/token gate cannot guarantee an exact dollar ceiling inside a running model request. Unknown usage halts further paid dispatch. Use provider-side spending controls for actual billing caps; subscription usage is not necessarily API dollars. No current API tariff is assumed or hardcoded.

Required future behavior: preserve timeouts and malformed output without silent retries; prevent duplicate dispatch with atomic state and a single-runner lock; inspect stale locks instead of deleting them automatically. A STOP file must prevent new dispatch; in-flight work can still incur usage. These controls require testing before any run. No background service or unattended paid run has been started.

## Runtime boundary

The verified local CLI supports explicit model selection, noninteractive JSON output and a final-output schema. The adapter invokes a subprocess argument list with a read-only sandbox and fresh/ephemeral session. It does not execute model-generated shell snippets supplied by result JSON. A CLI read-only sandbox is not a complete network/credential isolation guarantee; run unattended work under a research-only profile/account without trading connectors. This repository contains no order client. Any provider adapter must implement the same result contract, timeout and usage reporting before production use.

Sources checked September 2026: [official noninteractive CLI documentation](https://learn.chatgpt.com/docs/non-interactive-mode) and [official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents), plus installed `codex exec --help`. Documentation supports the runtime features; the persistent research state machine and gate design are this project's implementation choices. No claim that the desktop's internal collaboration tools are a portable SDK.

See `AGENT_WORKFLOW.md` for the original four research roles and file ownership, and `MODEL_EVALUATION.md` for worker calibration. Read `START_HERE.md` to replace the director without inheriting its conversation.
