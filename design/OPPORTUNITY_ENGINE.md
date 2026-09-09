# Opportunity research engine: authoritative direction

User direction adopted September 9, 2026. This document defines the target mission and next implementation sequence. It does not claim the continuing autonomous loop is implemented. Preserve the scientific controls, frozen research plans, evidence gates, context separation and versioned improvement machinery already present.

## Mission and terminal product

Discover opportunities with a plausible path to profitable, autonomously executable online systems. Trading is the initial and likely primary domain, not the core engine's permanent boundary. Equities, crypto, prediction markets, other financial markets, marketplace inefficiencies and automated online services are possible domains. Unconventional ideas remain eligible when their mechanism is coherent and testable.

This repository produces **implementation-ready opportunity blueprints**. A separate builder system owns production architecture, implementation, deployment and operation. Research code, test harnesses and adapters may live here; the final money-making systems do not become this repository's runtime.

Existing $2,500 capital, cash/whole-share and drawdown assumptions remain binding on their frozen trading experiments. They are not universal constraints on every future domain. New domain protocols must declare their own costs, observable outcomes, timing, execution constraints and validation requirements before testing.

## Continuing research loop

Generate ideas -> sanity check -> deduplicate -> categorize -> rank -> research -> test -> reject or advance -> validate -> blueprint -> repeat.

Creative generation receives the mission, useful lessons and enough context to avoid known repetitions. It is not burdened with every downstream implementation constraint. A separate sanity check filters incoherent mechanisms, impossible dependencies and absent paths to action before expensive work. Unusual is not a rejection reason. Missing evidence can mean blocked or inconclusive rather than false.

The global director manages the opportunity portfolio and available research capacity. Eventually, spare capacity should trigger a bounded generation batch automatically, subject to the deterministic budget and queue controls. Empty polling need not invoke a model. No fixed equal allocation across domains: productive areas can earn more research capacity, with an explicit, bounded allowance for new directions. Rank for value of further information and plausible net economics, not persuasive prose or selected historical returns.

## Durable idea and family memory

Extend the existing SQLite record with versioned opportunities and mechanism families. Retain idea text, domain, mechanism, affected participants, constraint/delay, path to autonomous execution, assumptions, source provenance, status, related IDs, resource use and reopening conditions.

Exact text matches are only the first check. Mechanism similarity must catch rewordings, parameter changes and alternate instruments expressing the same hypothesis. Similarity search proposes links; a reviewed decision records duplicate, variant, related-but-distinct or new family, with reasons. Do not erase unconventional ideas through an opaque similarity cutoff. Preserve every original submission and lineage even when merged for scheduling.

Failures and blockers are searchable records, not just the latest role memory. Reopening requires new evidence or a documented correction and creates a new linked version. Periodically distill recurring patterns into versioned lessons with supporting and counterexample IDs. Workers receive bounded relevant lessons, not the entire archive. Distilled memory never replaces source evidence or silently changes a failed result.

## Hierarchy and alignment

The internal director owns the global mission and portfolio. Workers receive a narrow role objective, the common opportunity/version identifier, relevant constraints and bounded evidence. Their success is accurate local scientific work. A correct rejection, block or falsification counts as success; workers are not rewarded for making candidates profitable.

The coding maintainer builds the system. The internal director operates it. Deterministic controls retain authority over budgets, state transitions, provenance and validation rules. The director integrates partial views but cannot waive these controls through a prompt or result.

## Three separate improvement mechanisms

1. **Memory/context:** improve retrieval, source-linked lessons and context assembly; preserve factual uncertainty and contradictory cases.
2. **Prompts:** director reviews recurring failure patterns across independent tasks before proposing a change. One poor answer alone does not trigger automatic rewriting. A proposal records supporting task IDs, frequency, affected role, counterexamples and expected regression risks. Preserve frozen comparisons, independent evaluation, version history and rollback.
3. **Routing:** evaluate model/role assignments using measured evidence fidelity, critical errors, rework and actual cost. Version routing policy separately from prompts. Compare on representative independent tasks; changing model, prompt and retrieval together requires attribution-aware evaluation rather than crediting one component without evidence.

The current gate tests are synthetic software tests, not evidence that any model stack or prompt is superior. Existing promotion APIs do not yet enforce recurring-pattern thresholds; implement that admission rule before automatic proposals. Domain-specific strategy mutations remain new scientific trials and require fresh confirmation under existing controls.

## Intended configurable model stack

User preferences, not verified provider model IDs, availability or prices:

- Normal orchestration: GPT-5.6 Sol.
- Difficult/high-value escalation: GPT-6 Astra.
- Inexpensive high-volume creativity/research: Meta Muse Spark.
- Independent checking/auditing: Grok.
- Adversarial/falsification work: Claude Sonnet-class models.

Resolve exact callable IDs and measure quality/cost when adapters are built. Keep capabilities and routing configurable; fail visibly when a configured provider is unavailable. Do not silently substitute providers, buy subscriptions or change spending limits. Diversity supplies different perspectives, not proof of independent errors or higher accuracy.

## Blueprint and builder feedback contract

A versioned blueprint must specify the opportunity/mechanism, evidence and provenance, target domain, validated scope, frozen behavior, inputs and knowledge timing, data dependencies, execution requirements, costs/unit economics, risk/failure limits, test results, untouched validation, unresolved limitations, monitoring and acceptance criteria. Include reproducible research artifacts and hashes, blueprint version and exact scientific decisions the builder must preserve. Domain-specific validation replaces irrelevant market-only tests, not the requirement for rigorous evidence.

The builder can submit a structured clarification referencing blueprint ID/version, exact ambiguous assumption, observed conflict, proposed alternatives and impact. The research system responds with a recorded clarification or a new version after appropriate revalidation. Builders must not silently reinterpret strategy rules. Production observations return as attributed feedback with deployment/version, conditions, costs, failures and deviations; they inform future ranking without rewriting historical outcomes.

## Next implementation sequence

1. Persist a canonical mission/portfolio record, domain-neutral opportunity/family registry and blueprint/clarification schemas. Preserve existing B3 IDs and frozen files.
2. Add creative generation, independent sanity check, reviewed semantic family linking and ranking packets around the current bounded evidence workflow. Test diverse synthetic domain cases and cheap rejection paths.
3. Add source-linked recurring-pattern/lesson records and separate evaluated routing versions. Require pattern evidence before automatic prompt-change proposals.
4. Implement one bounded provider adapter and real usage/identity controls; expand to the preferred diverse stack after verifying access and calibration.
5. Connect ready-work events and capacity refill under finite budgets. Test restart, duplicate generation, starvation, failure accounting and escalation before unattended operation.
6. Export reviewed blueprints and exercise the builder clarification/feedback protocol. Production deployment remains a separate system.

Current manual CEF workflow stays usable throughout this evolution. No automatic generation, semantic deduplication, multi-provider runtime, blueprint qualification or production deployment is established merely by adding this direction document.
