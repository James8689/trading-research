# Agent research system: design specification

Status: instructions and scaffold, not a deployed service. Read `STATUS.md` for the authoritative checkpoint. Existing runner code is unverified and should not influence scientific rules.

The system should optimize **reliable new evidence per unit of research cost**. A large agent population is not itself useful. Start with one frontier director and a small worker pool; create more independent narrow assignments only if measured quality and throughput justify it. Never promise that enough cycles will find a profitable strategy.

## Specification map

- `NETWORK.md`: roles, model tiers, decision rights and delegation.
- `CONTEXT_AND_RECOVERY.md`: worker-owned memory, small director context and interruption recovery.
- `RESEARCH_LIFECYCLE.md`: gates, failed ideas, holdout isolation and stopping.
- `COST_AND_SCHEDULING.md`: task economics, budgets, escalation and bounded cycles.
- `IMPLEMENTATION_HANDOFF.md`: later build sequence and acceptance scenarios.
- `EXTERNAL_CLAIM_REVIEW.md`: evidence review of the ten-agent memecoin story and reusable lessons.
- `SHADOW_STAGE_NETWORK.md`: future no-order signal/risk/liquidity/execution/accounting roles.
- `PERFORMANCE_CLAIM_STANDARD.md`: required proof before calling any result profitable or validated.
- `templates/`: copyable task, result, gate, candidate and resume documents. Samples describe fields; they are not live queue entries or evidence.

Original role prompts remain under `agents/prompts/`. The design extends these roles with later data extraction, offline engineering and independent validation functions. Model names live in configuration; portable role contracts do not depend on a provider or this conversation.

## Operating modes

1. **Design (current):** write/review specifications, templates and handoffs; no runtime activation.
2. **Assisted research:** a coding agent acts as director, creates bounded packets, delegates allowed work, validates artifacts and saves decisions. Requires a subsequent research instruction.
3. **Bounded unattended research (future):** tested controller dispatches a finite work queue inside an explicitly allocated budget. Pauses for unresolved gates and external dependencies; does not run an endless agent conversation.

Switching modes is recorded in an authorization record. A model cannot grant itself spending, paid data, account access, holdout access or trading authority. Existing research authorization does not override the latest design-only scope.
