# Agent research system: design specification

Status: broader design specification with a supported manual v1 now implemented. Read `STATUS.md` and `../docs/ORCHESTRATION.md` for tested capabilities and entry points. The legacy runner remains superseded and must not influence scientific rules.

The system should optimize **reliable new evidence per unit of research cost**. A large agent population is not itself useful. Start with one frontier director and a small worker pool; create more independent narrow assignments only if measured quality and throughput justify it. Never promise that enough cycles will find a profitable strategy.

## Specification map

- `OPPORTUNITY_ENGINE.md`: authoritative mission, creative discovery loop, family memory, distinct learning mechanisms and separate-builder blueprint boundary.

- `NETWORK.md`: roles, model tiers, decision rights and delegation.
- `CONTEXT_AND_RECOVERY.md`: worker-owned memory, small director context and interruption recovery.
- `RESEARCH_LIFECYCLE.md`: gates, failed ideas, holdout isolation and stopping.
- `COST_AND_SCHEDULING.md`: task economics, budgets, escalation and bounded cycles.
- `IMPLEMENTATION_HANDOFF.md`: later build sequence and acceptance scenarios.
- `EXTERNAL_CLAIM_REVIEW.md`: evidence review of the ten-agent memecoin story and reusable lessons.
- `SHADOW_STAGE_NETWORK.md`: future no-order signal/risk/liquidity/execution/accounting roles.
- `PERFORMANCE_CLAIM_STANDARD.md`: required proof before calling any result profitable or validated.
- `POST_INTEGRATION.md`: September 9 source review and proposed intake, budget-controller and attempt-lineage requirements.
- `POST_INTEGRATION_REVIEW.md`: independent gap review and concrete future acceptance scenarios for those requirements.
- `templates/`: copyable task, result, gate, candidate and resume documents. Samples describe fields; they are not live queue entries or evidence.

Original role prompts remain under `agents/prompts/`. The design extends these roles with later data extraction, offline engineering and independent validation functions. Model names live in configuration; portable role contracts do not depend on a provider or this conversation.

## Operating modes

1. **Design:** write/review specifications, templates and handoffs.
2. **Assisted research (manual v1 implemented):** an internal director identity handles research and prompt proposals through bounded packets. The coding maintainer builds the controller separately. No provider is dispatched automatically.
3. **Bounded unattended research (future):** tested controller dispatches a finite work queue inside an explicitly allocated budget. Pauses for unresolved gates and external dependencies; does not run an endless agent conversation.

Switching modes is recorded in an authorization record. A model cannot grant itself spending, paid data, account access, holdout access or trading authority. Existing research authorization does not override the latest design-only scope.
